"""
Modul: Responder — automatické odpovědi na emaily.

Aktivace: MODULES=responder (nebo responder,sorter,...)

Rozhraní:
  setup(app)          — zaregistruje Telegram handlery (/yes, /no)
  run(bot, email)     — zpracuje jeden email (klasifikace → draft → schválení → odeslání)
"""
import asyncio
import json
import logging
import os
from datetime import datetime, timezone

from src.config import RESPONDER_HISTORY_LOG
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
AUTO_RESPOND = os.getenv("AUTO_RESPOND", "false").lower() == "true"


def setup(app):
    """Zaregistruje /yes a /no handlery do Telegram aplikace."""
    app.add_handler(CommandHandler("yes", _cmd_yes))
    app.add_handler(CommandHandler("no", _cmd_no))
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    set_unpin_callback(lambda msg_id: app.bot.unpin_chat_message(chat_id=chat_id, message_id=msg_id))
    logger.info("Modul responder: inicializován.")


FOLDER_UNKNOWN = os.getenv("RESPONDER_UNKNOWN", "agent-unknown")
FOLDER_ESCALATED = os.getenv("RESPONDER_ESCALATED", "agent-escalated")

HISTORY_FILE = RESPONDER_HISTORY_LOG


def _log_response(email: dict, email_type: str, outcome: str, draft: str = "", auto_mode: bool = False):
    """Uloží výsledek zpracování emailu do logs/responder/responses.jsonl."""
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "time": datetime.now(timezone.utc).isoformat(),
        "from": email.get("from", ""),
        "subject": email.get("subject", ""),
        "body": email.get("body", ""),
        "type": email_type,
        "outcome": outcome,
        "auto_mode": auto_mode,
        "draft": draft,
    }
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


async def run(bot, email):
    """Zpracuje jeden email."""
    logger.info(f"[responder] Zpracovávám: '{email['subject']}' od {email['from']}")

    email_type = classify_email(email)

    if email_type == UNKNOWN_TYPE:
        mark_as_processed(email["id"], folder=FOLDER_UNKNOWN)
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
        _log_response(email, "UNK", "unknown", auto_mode=True)
        return

    if email_type == ESCALATION_TYPE:
        mark_as_processed(email["id"], folder=FOLDER_ESCALATED)
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
        _log_response(email, "ESC", "escalated", auto_mode=True)
        return

    mark_as_processed(email["id"])

    if email_type not in AUTO_REPLY_TYPES:
        logger.info(f"[responder] Neznámý typ '{email_type}' — přeskakuji.")
        return

    draft = generate_reply(email, email_type)

    if DRY_RUN:
        logger.info(f"[responder] [DRY RUN] Draft:\n{draft}\n---")
        _log_response(email, email_type, "dry_run", draft, auto_mode=False)
        return

    if AUTO_RESPOND:
        send_reply(email, draft)
        logger.info(f"[responder] [AUTO] Email odeslán bez schválení.")
        _log_response(email, email_type, "auto", draft, auto_mode=True)
        return

    await send_approval_request(bot, email, email_type, draft)
    approved = await wait_for_approval(bot)

    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if approved is None:
        logger.info("[responder] Timeout — email vrácen do fronty.")
        _log_response(email, email_type, "timeout", draft, auto_mode=False)
    elif approved:
        await bot.send_message(chat_id=chat_id, text="👍 Odesílám...")
        send_reply(email, draft)
        await bot.send_message(chat_id=chat_id, text="✅ Email byl odeslán.")
        logger.info("[responder] Email odeslán.")
        _log_response(email, email_type, "approved", draft, auto_mode=False)
    else:
        await bot.send_message(chat_id=chat_id, text="❌ Email přeskočen.")
        logger.info("[responder] Email zamítnut.")
        _log_response(email, email_type, "rejected", draft, auto_mode=False)


async def run_batch(bot, emails: list):
    """
    Zpracuje seznam emailů efektivně:
    1. Klasifikuje všechny emaily
    2. Generuje drafty paralelně (asyncio.gather)
    3. Prezentuje schválení sekvenčně — bez čekání na LLM mezi emaily
    """
    classified = []
    for email in emails:
        email_type = classify_email(email)

        if email_type == UNKNOWN_TYPE:
            mark_as_processed(email["id"], folder=FOLDER_UNKNOWN)
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
            _log_response(email, "UNK", "unknown", auto_mode=True)
            continue

        if email_type == ESCALATION_TYPE:
            mark_as_processed(email["id"], folder=FOLDER_ESCALATED)
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
            _log_response(email, "ESC", "escalated", auto_mode=True)
            continue

        mark_as_processed(email["id"])

        if email_type not in AUTO_REPLY_TYPES:
            logger.info(f"[responder] Neznámý typ '{email_type}' — přeskakuji.")
            continue

        classified.append((email, email_type))

    if not classified:
        return

    if DRY_RUN:
        for email, email_type in classified:
            draft = generate_reply(email, email_type)
            logger.info(f"[responder] [DRY RUN] Draft:\n{draft}\n---")
            _log_response(email, email_type, "dry_run", draft)
        return

    # Generuj všechny drafty paralelně
    logger.info(f"[responder] Generuji {len(classified)} draft(ů) paralelně...")
    loop = asyncio.get_running_loop()
    drafts = await asyncio.gather(*[
        loop.run_in_executor(None, generate_reply, email, email_type)
        for email, email_type in classified
    ], return_exceptions=True)

    if AUTO_RESPOND:
        for (email, email_type), draft in zip(classified, drafts):
            if isinstance(draft, Exception):
                logger.error(f"[responder] generate_reply selhal pro '{email['subject']}': {draft}")
                _log_response(email, email_type, "unknown", auto_mode=True)
                continue
            try:
                send_reply(email, draft)
                logger.info(f"[responder] [AUTO] Odesláno: '{email['subject']}'")
                _log_response(email, email_type, "auto", draft)
            except Exception as e:
                logger.error(f"[responder] send_reply selhal pro '{email['subject']}': {e}")
                _log_response(email, email_type, "unknown", draft, auto_mode=True)
        return

    # Prezentuj schválení sekvenčně — drafty jsou už hotové
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    for (email, email_type), draft in zip(classified, drafts):
        await send_approval_request(bot, email, email_type, draft)
        approved = await wait_for_approval(bot)

        if approved is None:
            logger.info("[responder] Timeout — přeskakuji.")
            _log_response(email, email_type, "timeout", draft, auto_mode=False)
        elif approved:
            await bot.send_message(chat_id=chat_id, text="👍 Odesílám...")
            send_reply(email, draft)
            await bot.send_message(chat_id=chat_id, text="✅ Email byl odeslán.")
            logger.info("[responder] Email odeslán.")
            _log_response(email, email_type, "approved", draft, auto_mode=False)
        else:
            await bot.send_message(chat_id=chat_id, text="❌ Email přeskočen.")
            logger.info("[responder] Email zamítnut.")
            _log_response(email, email_type, "rejected", draft, auto_mode=False)


# --- Telegram handlery ---

async def _cmd_yes(update, context):
    await resolve_approval(True)


async def _cmd_no(update, context):
    await resolve_approval(False)
    await update.message.reply_text("👎 Přeskočeno.")
