"""
Mail client — Helpdesk API (Zendesk / Freshdesk)

Nepracuje s e-mailem přímo — čte a odpovídá na tikety přes REST API.
Nový email od zákazníka se v helpdesku automaticky stane tiketem.

Rozhraní:
  get_unprocessed_emails() -> list[dict]
  mark_as_processed(email_id: str)
  send_reply(email: dict, text: str)

Env proměnné (Zendesk):
  HELPDESK_PROVIDER   (zendesk nebo freshdesk)
  HELPDESK_SUBDOMAIN  (např. firma → firma.zendesk.com)
  HELPDESK_EMAIL
  HELPDESK_API_TOKEN

Jak získat API token:
  Zendesk:   Admin → Apps & Integrations → Zendesk API → Add API token
  Freshdesk: Profile Settings → API Key
"""
import logging
import os

import requests

logger = logging.getLogger(__name__)

PROVIDER = os.getenv("HELPDESK_PROVIDER", "zendesk")
SUBDOMAIN = os.getenv("HELPDESK_SUBDOMAIN", "")
HD_EMAIL = os.getenv("HELPDESK_EMAIL", "")
API_TOKEN = os.getenv("HELPDESK_API_TOKEN", "")


def _zendesk_headers() -> dict:
    return {"Content-Type": "application/json"}


def _zendesk_auth():
    return (f"{HD_EMAIL}/token", API_TOKEN)


def _freshdesk_headers() -> dict:
    return {"Content-Type": "application/json"}


def _freshdesk_auth():
    return (API_TOKEN, "X")  # Freshdesk: API key jako username, heslo cokoliv


def get_unprocessed_emails() -> list[dict]:
    """Vrátí otevřené tikety čekající na odpověď agenta."""
    if PROVIDER == "zendesk":
        url = f"https://{SUBDOMAIN}.zendesk.com/api/v2/tickets.json"
        params = {"status": "new,open"}
        resp = requests.get(url, headers=_zendesk_headers(), auth=_zendesk_auth(), params=params)
        resp.raise_for_status()
        tickets = resp.json().get("tickets", [])
        emails = [{
            "id": str(t["id"]),
            "thread_id": str(t["id"]),
            "from": t.get("requester_id", ""),
            "to": HD_EMAIL,
            "subject": t.get("subject", ""),
            "date": t.get("created_at", ""),
            "body": t.get("description", ""),
        } for t in tickets]

    elif PROVIDER == "freshdesk":
        url = f"https://{SUBDOMAIN}.freshdesk.com/api/v2/tickets"
        params = {"status": 2}  # 2 = Open
        resp = requests.get(url, headers=_freshdesk_headers(), auth=_freshdesk_auth(), params=params)
        resp.raise_for_status()
        tickets = resp.json()
        emails = [{
            "id": str(t["id"]),
            "thread_id": str(t["id"]),
            "from": t.get("requester_id", ""),
            "to": HD_EMAIL,
            "subject": t.get("subject", ""),
            "date": t.get("created_at", ""),
            "body": t.get("description_text", ""),
        } for t in tickets]

    else:
        raise ValueError(f"Nepodporovaný helpdesk provider: {PROVIDER}")

    logger.info(f"Nalezeno {len(emails)} tiketů k zpracování ({PROVIDER}).")
    return emails


def mark_as_processed(email_id: str):
    """Přidá interní tag 'agent-processed' na tiket."""
    if PROVIDER == "zendesk":
        url = f"https://{SUBDOMAIN}.zendesk.com/api/v2/tickets/{email_id}.json"
        requests.put(url, headers=_zendesk_headers(), auth=_zendesk_auth(), json={
            "ticket": {"tags": ["agent-processed"]}
        }).raise_for_status()

    elif PROVIDER == "freshdesk":
        url = f"https://{SUBDOMAIN}.freshdesk.com/api/v2/tickets/{email_id}"
        requests.put(url, headers=_freshdesk_headers(), auth=_freshdesk_auth(), json={
            "tags": ["agent-processed"]
        }).raise_for_status()

    logger.debug(f"Tiket {email_id} označen jako zpracovaný ({PROVIDER}).")


def send_reply(email_data: dict, text: str):
    """Přidá veřejnou odpověď (reply) na tiket."""
    ticket_id = email_data["id"]

    if PROVIDER == "zendesk":
        url = f"https://{SUBDOMAIN}.zendesk.com/api/v2/tickets/{ticket_id}.json"
        requests.put(url, headers=_zendesk_headers(), auth=_zendesk_auth(), json={
            "ticket": {"comment": {"body": text, "public": True}}
        }).raise_for_status()

    elif PROVIDER == "freshdesk":
        url = f"https://{SUBDOMAIN}.freshdesk.com/api/v2/tickets/{ticket_id}/reply"
        requests.post(url, headers=_freshdesk_headers(), auth=_freshdesk_auth(), json={
            "body": text
        }).raise_for_status()

    logger.info(f"Odpověď přidána na tiket {ticket_id} ({PROVIDER}).")
