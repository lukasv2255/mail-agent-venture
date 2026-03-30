"""
Telegram notifier — pošle draft odpovědi a čeká na potvrzení.
Sdílí jednu PTB Application instanci s main.py.
"""
import asyncio
import logging
import os

logger = logging.getLogger(__name__)

# Globální future pro čekání na /yes nebo /no
_pending_approval: asyncio.Future | None = None


def set_pending_approval(future: asyncio.Future):
    global _pending_approval
    _pending_approval = future


async def send_approval_request(bot, email, email_type, draft_reply):
    """Pošle návrh odpovědi do Telegramu."""
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


async def wait_for_approval(timeout_seconds=300):
    """
    Čeká na /yes nebo /no z Telegramu přes sdílené Future.
    Vrátí True nebo False.
    """
    loop = asyncio.get_event_loop()
    future = loop.create_future()
    set_pending_approval(future)

    logger.info(f"Čekám na potvrzení přes Telegram (timeout: {timeout_seconds}s)...")
    try:
        return await asyncio.wait_for(future, timeout=timeout_seconds)
    except asyncio.TimeoutError:
        logger.warning("Timeout — email nebyl odeslán.")
        return False
    finally:
        set_pending_approval(None)


async def resolve_approval(approved: bool):
    """Zavolá se z /yes nebo /no handleru."""
    global _pending_approval
    if _pending_approval and not _pending_approval.done():
        _pending_approval.set_result(approved)
