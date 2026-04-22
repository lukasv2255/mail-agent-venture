"""
Mail client abstrakce — přepíná implementaci podle MAIL_CLIENT env proměnné.

Dostupné hodnoty MAIL_CLIENT:
  gmail     — Gmail API (OAuth2), výchozí
  imap      — univerzální IMAP + SMTP
  graph     — Microsoft Graph (Outlook / Office 365)
  helpdesk  — Zendesk nebo Freshdesk

Rozhraní (stejné pro všechny implementace):
  get_unprocessed_emails() -> list[dict]
  mark_as_processed(email_id: str)
  send_reply(email: dict, text: str)
"""
import importlib
import os

_PROVIDERS = {
    "gmail": "src.mail_client_gmail",
    "imap": "src.mail_client_imap",
    "graph": "src.mail_client_graph",
    "helpdesk": "src.mail_client_helpdesk",
}


def _get_provider():
    provider = os.getenv("MAIL_CLIENT", "gmail")
    if provider not in _PROVIDERS:
        raise ValueError(
            f"Neznámý MAIL_CLIENT='{provider}'. Možnosti: {list(_PROVIDERS)}"
        )
    return importlib.import_module(_PROVIDERS[provider])


def get_unprocessed_emails() -> list[dict]:
    return _get_provider().get_unprocessed_emails()


def mark_as_processed(email_id: str, folder: str = None):
    _get_provider().mark_as_processed(email_id, folder=folder)


def send_reply(email: dict, text: str):
    _get_provider().send_reply(email, text)
