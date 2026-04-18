"""
Modul: Responder — automatické odpovědi na emaily.

Aktivace: MODULES=responder (nebo responder,sorter,...)

Rozhraní:
  setup(app)          — zaregistruje Telegram handlery (/yes, /no)
  run(bot, email)     — zpracuje jeden email (klasifikace → draft → schválení → odeslání)
"""
import asyncio
import logging
import os

from src.classifier import classify_email, UNKNOWN_TYPE, ESCALATION_TYPE, AUTO_REPLY_TYPES
from src.mail_client import mark_as_processed, send_reply
from src.notifier import (
    send_approval_request, wait_for_approval, resolve_approval,
    add_alert, set_unpin_callback,
)

# Přímý import generate_reply ze stávajícího src/responder.py
from src.responder import generate_reply

from telegram.ext import CommandHandler

logger = logging.getLogger(__name__)

DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"


def setup(app):
    """Zaregistruje /yes a /no handlery do Telegram aplikace."""
    app.add_handler(CommandHandler("yes", _cmd_yes))
    app.add_handler(CommandHandler("no", _cmd_no))
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    set_unpin_callback(lambda msg_id: app.bot.unpin_chat_message(chat_id=chat_id, message_id=msg_id))
    logger.info("Modul responder: inicializován.")


async def run(bot, email):
    """Zpracuje jeden email."""
    logger.info(f"[responder] Zpracovávám: '{email['subject']}' od {email['from']}")
    mark_as_processed(email["id"])

    email_type = classify_email(email)

    if email_type == UNKNOWN_TYPE:
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        msg = await bot.send_message(
            chat_id=chat_id,
            text=(
                f"⚪ Nezpracováno (UNK)\n"
                f"Od: {email['from']}\n"
                f"Předmět: {email['subject']}\n\n"
                f"{email['body'][:300]}"
            )
        )
        await bot.pin_chat_message(chat_id=chat_id, message_id=msg.message_id, disable_notification=True)
        add_alert(email, "UNK", message_id=msg.message_id)
        return

    if email_type == ESCALATION_TYPE:
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        msg = await bot.send_message(
            chat_id=chat_id,
            text=(
                f"🚨 Eskalace — vyžaduje lidskou reakci\n"
                f"Od: {email['from']}\n"
                f"Předmět: {email['subject']}\n\n"
                f"{email['body'][:300]}"
            )
        )
        await bot.pin_chat_message(chat_id=chat_id, message_id=msg.message_id, disable_notification=True)
        add_alert(email, "ESC", message_id=msg.message_id)
        return

    if email_type not in AUTO_REPLY_TYPES:
        logger.info(f"[responder] Neznámý typ '{email_type}' — přeskakuji.")
        return

    draft = generate_reply(email, email_type)

    if DRY_RUN:
        logger.info(f"[responder] [DRY RUN] Draft:\n{draft}\n---")
        return

    await send_approval_request(bot, email, email_type, draft)
    approved = await wait_for_approval(bot)

    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if approved is None:
        logger.info("[responder] Timeout — email vrácen do fronty.")
    elif approved:
        await bot.send_message(chat_id=chat_id, text="👍 Odesílám...")
        send_reply(email, draft)
        await bot.send_message(chat_id=chat_id, text="✅ Email byl odeslán.")
        logger.info("[responder] Email odeslán.")
    else:
        await bot.send_message(chat_id=chat_id, text="❌ Email přeskočen.")
        logger.info("[responder] Email zamítnut.")


# --- Telegram handlery ---

async def _cmd_yes(update, context):
    await resolve_approval(True)


async def _cmd_no(update, context):
    await resolve_approval(False)
    await update.message.reply_text("👎 Přeskočeno.")
