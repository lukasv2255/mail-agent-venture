"""
Telegram notifier — pošle draft odpovědi a čeká na potvrzení.
Sdílí jednu PTB Application instanci s main.py.
"""
import asyncio
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

# Globální future pro čekání na /yes nebo /no
_pending_approval: Optional[asyncio.Future] = None

# Stav aktuálně čekajícího emailu — čte dashboard
_pending_item: Optional[dict] = None  # {"email": ..., "email_type": ..., "draft": ...}


def set_pending_approval(future: asyncio.Future):
    global _pending_approval
    _pending_approval = future


def set_pending_item(item: Optional[dict]):
    global _pending_item
    _pending_item = item


def get_pending_item() -> Optional[dict]:
    return _pending_item


async def send_approval_request(bot, email, email_type, draft_reply):
    """Pošle návrh odpovědi do Telegramu a uloží do sdíleného stavu pro dashboard."""
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    text = (
        f"📧 Nový email\n"
        f"Od: {email['from']}\n"
        f"Předmět: {email['subject']}\n"
        f"Typ: {email_type}\n\n"
        f"Navrhovaná odpověď:\n"
        f"---\n{draft_reply[:800]}\n---\n\n"
        f"Odpověz /yes (odeslat) nebo /no (přeskočit)"
    )
    await bot.send_message(chat_id=chat_id, text=text)
    set_pending_item({"email": email, "email_type": email_type, "draft": draft_reply})


async def wait_for_approval(bot, timeout_seconds=3600):
    """
    Čeká na /yes nebo /no z Telegramu přes sdílené Future.
    Vrátí True (schváleno), False (/no), nebo None (timeout — email vrátit do fronty).
    """
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    loop = asyncio.get_event_loop()
    future = loop.create_future()
    set_pending_approval(future)

    logger.info(f"Čekám na potvrzení přes Telegram (timeout: {timeout_seconds}s)...")
    try:
        return await asyncio.wait_for(future, timeout=timeout_seconds)
    except asyncio.TimeoutError:
        logger.warning("Timeout — email vrácen do fronty.")
        await bot.send_message(
            chat_id=chat_id,
            text="⏰ Čas na schválení vypršel. Email bude zpracován při příštím /check."
        )
        return None
    finally:
        set_pending_approval(None)
        set_pending_item(None)


async def resolve_approval(approved: bool):
    """Zavolá se z /yes nebo /no handleru."""
    global _pending_approval
    if _pending_approval and not _pending_approval.done():
        _pending_approval.set_result(approved)
