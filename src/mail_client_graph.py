"""
Mail client — Microsoft Graph API (Outlook / Office 365)

Rozhraní:
  get_unprocessed_emails() -> list[dict]
  mark_as_processed(email_id: str)
  send_reply(email: dict, text: str)

Autentizace: OAuth2 přes Azure app registration
Env proměnné:
  GRAPH_CLIENT_ID
  GRAPH_CLIENT_SECRET
  GRAPH_TENANT_ID
  GRAPH_USER_EMAIL    (e-mailová adresa která se monitoruje)

Jak získat credentials:
  1. Jdi na portal.azure.com → App registrations → New registration
  2. Přidej oprávnění: Mail.Read, Mail.Send, Mail.ReadWrite
  3. Vytvoř Client secret
  4. Zapiš Client ID, Client Secret, Tenant ID do env proměnných
"""
import logging
import os

import requests

logger = logging.getLogger(__name__)

CLIENT_ID = os.getenv("GRAPH_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("GRAPH_CLIENT_SECRET", "")
TENANT_ID = os.getenv("GRAPH_TENANT_ID", "")
USER_EMAIL = os.getenv("GRAPH_USER_EMAIL", "")

GRAPH_BASE = "https://graph.microsoft.com/v1.0"
PROCESSED_CATEGORY = "agent-processed"  # Outlook kategorie pro zpracované emaily


def _get_token() -> str:
    """Získá přístupový token přes client credentials flow."""
    url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    resp = requests.post(url, data={
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": "https://graph.microsoft.com/.default",
    })
    resp.raise_for_status()
    return resp.json()["access_token"]


def _headers() -> dict:
    return {"Authorization": f"Bearer {_get_token()}", "Content-Type": "application/json"}


def get_unprocessed_emails() -> list[dict]:
    """Vrátí emaily bez kategorie PROCESSED_CATEGORY."""
    url = f"{GRAPH_BASE}/users/{USER_EMAIL}/mailFolders/inbox/messages"
    params = {
        "$filter": f"not categories/any(c:c eq '{PROCESSED_CATEGORY}')",
        "$top": 20,
        "$select": "id,conversationId,from,toRecipients,subject,receivedDateTime,body",
    }
    resp = requests.get(url, headers=_headers(), params=params)
    resp.raise_for_status()

    emails = []
    for msg in resp.json().get("value", []):
        emails.append({
            "id": msg["id"],
            "thread_id": msg["conversationId"],
            "from": msg["from"]["emailAddress"]["address"],
            "to": USER_EMAIL,
            "subject": msg.get("subject", ""),
            "date": msg.get("receivedDateTime", ""),
            "body": msg["body"]["content"],
        })

    logger.info(f"Nalezeno {len(emails)} nezpracovaných emailů (Graph API).")
    return emails


def mark_as_processed(email_id: str):
    """Přidá kategorii PROCESSED_CATEGORY na email."""
    url = f"{GRAPH_BASE}/users/{USER_EMAIL}/messages/{email_id}"
    requests.patch(url, headers=_headers(), json={
        "categories": [PROCESSED_CATEGORY]
    }).raise_for_status()
    logger.debug(f"Email {email_id} označen jako zpracovaný (Graph API).")


def send_reply(email_data: dict, text: str):
    """Odešle odpověď na email přes Graph API."""
    url = f"{GRAPH_BASE}/users/{USER_EMAIL}/messages/{email_data['id']}/reply"
    requests.post(url, headers=_headers(), json={
        "message": {
            "body": {"contentType": "Text", "content": text}
        }
    }).raise_for_status()
    logger.info(f"Odpověď odeslána na {email_data['from']} (Graph API).")
