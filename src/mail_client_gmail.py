"""
Mail client — Gmail API

Rozhraní:
  get_unprocessed_emails() -> list[dict]
  mark_as_processed(email_id: str)
  send_reply(email: dict, text: str)

Autentizace: OAuth2 (credentials.json + token.json)
Env proměnné:
  GMAIL_CREDENTIALS_FILE  (default: credentials.json)
  GMAIL_TOKEN_FILE        (default: token.json)
  GMAIL_TOKEN_JSON        (base64 token pro Railway)
"""
from src.gmail_client import (
    get_gmail_service,
    get_unprocessed_emails as _get_unprocessed,
    mark_as_processed as _mark_as_processed,
    send_reply as _send_reply,
)

_service = None


def _get_service():
    global _service
    if _service is None:
        _service = get_gmail_service()
    return _service


def get_unprocessed_emails() -> list[dict]:
    return _get_unprocessed(_get_service())


def mark_as_processed(email_id: str):
    _mark_as_processed(_get_service(), email_id)


def send_reply(email: dict, text: str):
    _send_reply(_get_service(), email, text)
