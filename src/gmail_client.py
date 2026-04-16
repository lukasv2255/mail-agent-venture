"""
Gmail API client — čtení a odesílání emailů přes OAuth2.
"""
import base64
import logging
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

# Jaké oprávnění potřebujeme od Gmailu
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",  # pro přidávání labelů
]

PROCESSED_LABEL = "agent-processed"  # label pro zpracované emaily


def get_gmail_service():
    """Připojí se k Gmail API.

    Lokálně: načte token z token.json
    Railway: načte token z env proměnné GMAIL_TOKEN_JSON (base64)
    """
    creds = None
    token_file = os.getenv("GMAIL_TOKEN_FILE", "token.json")
    credentials_file = os.getenv("GMAIL_CREDENTIALS_FILE", "credentials.json")

    # Railway: token jako base64 env proměnná
    token_b64 = os.getenv("GMAIL_TOKEN_JSON")
    if token_b64:
        import json
        import tempfile
        token_data = base64.b64decode(token_b64).decode()
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        tmp.write(token_data)
        tmp.flush()
        creds = Credentials.from_authorized_user_file(tmp.name, SCOPES)
        token_file = tmp.name
    elif os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)

    # Pokud token expiroval, obnov ho
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            logger.info("Gmail token obnoven.")
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
            creds = flow.run_local_server(port=0)
            logger.info("Gmail OAuth flow dokončen.")

        with open(token_file, "w") as f:
            f.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def get_unprocessed_emails(service, max_results=20):
    """
    Vrátí nové emaily, které ještě nebyly zpracovány agentem.
    Pozná je tak, že nemají label PROCESSED_LABEL.
    """
    query = f"-label:{PROCESSED_LABEL} in:inbox"
    result = service.users().messages().list(
        userId="me", q=query, maxResults=max_results
    ).execute()

    messages = result.get("messages", [])
    emails = []
    for msg in messages:
        full_msg = service.users().messages().get(
            userId="me", id=msg["id"], format="full"
        ).execute()
        emails.append(parse_email(full_msg))

    logger.info(f"Nalezeno {len(emails)} nezpracovaných emailů.")
    return emails


def parse_email(raw_message):
    """Vytáhne z raw Gmail zprávy užitečná data."""
    headers = {h["name"]: h["value"] for h in raw_message["payload"]["headers"]}
    body = extract_body(raw_message["payload"])

    return {
        "id": raw_message["id"],
        "thread_id": raw_message["threadId"],
        "from": headers.get("From", ""),
        "to": headers.get("To", ""),
        "subject": headers.get("Subject", ""),
        "date": headers.get("Date", ""),
        "body": body,
    }


def extract_body(payload):
    """Rekurzivně vytáhne text z emailu (plain text preferovaný)."""
    if payload.get("body", {}).get("data"):
        return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")

    for part in payload.get("parts", []):
        if part["mimeType"] == "text/plain":
            data = part.get("body", {}).get("data", "")
            if data:
                return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

    # Fallback na HTML část
    for part in payload.get("parts", []):
        if part["mimeType"] == "text/html":
            data = part.get("body", {}).get("data", "")
            if data:
                return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

    return ""


def mark_as_processed(service, message_id):
    """Přidá label agent-processed, aby agent email zpracoval jen jednou."""
    label_id = get_or_create_label(service, PROCESSED_LABEL)
    service.users().messages().modify(
        userId="me",
        id=message_id,
        body={"addLabelIds": [label_id]},
    ).execute()
    logger.debug(f"Email {message_id} označen jako zpracovaný.")


def send_reply(service, original_email, reply_body):
    """Odešle odpověď na email ve stejném threadu."""
    message = MIMEMultipart()
    message["to"] = original_email["from"]
    message["subject"] = "Re: " + original_email["subject"]
    message["In-Reply-To"] = original_email["id"]
    message["References"] = original_email["id"]
    message.attach(MIMEText(reply_body, "plain", "utf-8"))

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    service.users().messages().send(
        userId="me",
        body={"raw": raw, "threadId": original_email["thread_id"]},
    ).execute()
    logger.info(f"Odpověď odeslána na {original_email['from']}.")


def get_or_create_label(service, label_name):
    """Vrátí ID labelu, nebo ho vytvoří pokud neexistuje."""
    labels = service.users().labels().list(userId="me").execute().get("labels", [])
    for label in labels:
        if label["name"] == label_name:
            return label["id"]

    new_label = service.users().labels().create(
        userId="me", body={"name": label_name}
    ).execute()
    logger.info(f"Vytvořen Gmail label: {label_name}")
    return new_label["id"]


if __name__ == "__main__":
    print("Spouštím Gmail OAuth flow...")
    service = get_gmail_service()
    print("✅ token.json vytvořen. Gmail API připojeno.")
