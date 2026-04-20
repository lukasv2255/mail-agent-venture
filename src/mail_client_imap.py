"""
Mail client — IMAP (univerzální)

Funguje s jakýmkoliv poskytovatelem: Gmail, Outlook, Seznam, vlastní server.
Gmail a Outlook vyžadují OAuth2 nebo App Password místo běžného hesla.

Rozhraní:
  get_unprocessed_emails() -> list[dict]
  mark_as_processed(email_id: str)
  send_reply(email: dict, text: str)

Env proměnné:
  IMAP_HOST      (např. imap.gmail.com, imap.seznam.cz)
  IMAP_PORT      (default: 993)
  IMAP_USER
  IMAP_PASSWORD
  SMTP_HOST      (pro odesílání, např. smtp.gmail.com)
  SMTP_PORT      (default: 587)
"""
import email
import email.header
import imaplib
import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)

IMAP_HOST = os.getenv("IMAP_HOST", "")
IMAP_PORT = int(os.getenv("IMAP_PORT", "993"))
IMAP_USER = os.getenv("IMAP_USER", "")
IMAP_PASSWORD = os.getenv("IMAP_PASSWORD", "")
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))

PROCESSED_FOLDER = os.getenv("IMAP_PROCESSED_FOLDER", "agent-processed")

# Složky které agent prohledává — oddělené čárkou, např. "INBOX,Ostatní"
_INBOX_FOLDERS = [f.strip() for f in os.getenv("IMAP_INBOX_FOLDERS", "INBOX").split(",")]


def _connect() -> imaplib.IMAP4_SSL:
    conn = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
    conn.login(IMAP_USER, IMAP_PASSWORD)
    return conn


def _ensure_folder(conn: imaplib.IMAP4_SSL, folder: str):
    """Vytvoří složku pokud neexistuje."""
    result = conn.list('""', folder)
    exists = result[1] and result[1][0] is not None and folder.encode() in result[1][0]
    if not exists:
        conn.create(folder)
        logger.info(f"Vytvořena IMAP složka: {folder}")


def get_unprocessed_emails() -> list[dict]:
    """Vrátí všechny emaily ze sledovaných složek (IMAP_INBOX_FOLDERS)."""
    conn = _connect()

    emails = []
    for folder in _INBOX_FOLDERS:
        result, _ = conn.select(folder)
        if result != "OK":
            logger.warning(f"Složka '{folder}' neexistuje nebo není přístupná.")
            continue

        _, data = conn.uid("SEARCH", None, "ALL")
        uids = data[0].split()

        for uid in uids:
            _, msg_data = conn.uid("FETCH", uid, "(RFC822)")
            raw = msg_data[0][1]
            msg = email.message_from_bytes(raw)
            emails.append({
                "id": uid.decode(),
                "folder": folder,
                "thread_id": msg.get("Message-ID", ""),
                "from": _decode_header(msg.get("From", "")),
                "to": _decode_header(msg.get("To", "")),
                "subject": _decode_header(msg.get("Subject", "")),
                "date": msg.get("Date", ""),
                "body": _extract_body(msg),
            })

    conn.logout()
    logger.info(f"Nalezeno {len(emails)} nezpracovaných emailů (IMAP, složky: {_INBOX_FOLDERS}).")
    return emails


def mark_as_processed(email_id: str, folder: str = None, source_folder: str = "INBOX"):
    """Přesune email do zadané složky (default: PROCESSED_FOLDER)."""
    target = folder or PROCESSED_FOLDER
    conn = _connect()
    _ensure_folder(conn, target)
    conn.select(source_folder)
    # UID COPY/STORE — stabilní i po smazání předchozích zpráv
    conn.uid("COPY", email_id.encode(), target)
    conn.uid("STORE", email_id.encode(), "+FLAGS", "\\Deleted")
    conn.expunge()
    conn.logout()
    logger.debug(f"Email UID {email_id} přesunut z '{source_folder}' do '{target}'.")


def send_reply(email_data: dict, text: str):
    """Odešle odpověď přes SMTP."""
    msg = MIMEMultipart()
    msg["From"] = IMAP_USER
    msg["To"] = email_data["from"]
    msg["Subject"] = "Re: " + email_data["subject"]
    msg["In-Reply-To"] = email_data["thread_id"]
    msg["References"] = email_data["thread_id"]
    msg.attach(MIMEText(text, "plain", "utf-8"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(IMAP_USER, IMAP_PASSWORD)
        server.send_message(msg)

    logger.info(f"Odpověď odeslána na {email_data['from']} (SMTP).")


def _decode_header(value: str) -> str:
    """Dekóduje RFC 2047 hlavičku (=?utf-8?q?...?=) na čitelný text."""
    parts = email.header.decode_header(value)
    decoded = []
    for part, charset in parts:
        if isinstance(part, bytes):
            decoded.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            decoded.append(part)
    return " ".join(decoded)


def _extract_body(msg) -> str:
    """Vytáhne plain text tělo emailu."""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    return payload.decode("utf-8", errors="replace")
    payload = msg.get_payload(decode=True)
    if payload:
        return payload.decode("utf-8", errors="replace")
    return ""
