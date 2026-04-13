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

# IMAP flag pro označení zpracovaných emailů
PROCESSED_FLAG = "agent-processed"


def _connect() -> imaplib.IMAP4_SSL:
    conn = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
    conn.login(IMAP_USER, IMAP_PASSWORD)
    return conn


def get_unprocessed_emails() -> list[dict]:
    """Vrátí emaily z inboxu bez custom flagu PROCESSED_FLAG."""
    conn = _connect()
    conn.select("INBOX")

    # Hledáme nepřečtené nebo nezpracované — bez custom keyword flagu
    # Poznámka: custom keyword flagy (IMAP keywords) musí server podporovat
    _, data = conn.search(None, "UNSEEN")
    email_ids = data[0].split()

    emails = []
    for eid in email_ids:
        _, msg_data = conn.fetch(eid, "(RFC822)")
        raw = msg_data[0][1]
        msg = email.message_from_bytes(raw)
        emails.append({
            "id": eid.decode(),
            "thread_id": msg.get("Message-ID", ""),
            "from": msg.get("From", ""),
            "to": msg.get("To", ""),
            "subject": msg.get("Subject", ""),
            "date": msg.get("Date", ""),
            "body": _extract_body(msg),
        })

    conn.logout()
    logger.info(f"Nalezeno {len(emails)} nezpracovaných emailů (IMAP).")
    return emails


def mark_as_processed(email_id: str):
    """Označí email jako přečtený (SEEN). Alternativa: přesunout do složky."""
    conn = _connect()
    conn.select("INBOX")
    conn.store(email_id.encode(), "+FLAGS", "\\Seen")
    conn.logout()
    logger.debug(f"Email {email_id} označen jako zpracovaný (IMAP).")


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


def _extract_body(msg) -> str:
    """Vytáhne plain text tělo emailu."""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                return part.get_payload(decode=True).decode("utf-8", errors="replace")
    return msg.get_payload(decode=True).decode("utf-8", errors="replace")
