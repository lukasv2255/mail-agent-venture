"""
E-mailový agent — hlavní vstupní bod.

Spuštění:
  python main.py    # spustí agenta s Telegram botem a schedulingem
"""
import asyncio
import logging
import os

from dotenv import load_dotenv

load_dotenv()

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from src.mail_client import get_unprocessed_emails, mark_as_processed, send_reply
from src.classifier import classify_email, UNKNOWN_TYPE, ESCALATION_TYPE, AUTO_REPLY_TYPES
from src.responder import generate_reply
from src.notifier import send_approval_request, wait_for_approval, resolve_approval

os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/agent.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL_MINUTES", "60")) * 60

MAIL_CLIENT = os.getenv("MAIL_CLIENT", "gmail")
MAIL_ADDRESS = {
    "gmail": os.getenv("GMAIL_ADDRESS", "—"),
    "imap": os.getenv("IMAP_USER", "—"),
    "graph": os.getenv("GRAPH_USER_EMAIL", "—"),
    "helpdesk": os.getenv("HELPDESK_EMAIL", "—"),
}.get(MAIL_CLIENT, "—")

# Zámek aby nespustily dva checy najednou
_check_lock = asyncio.Lock()


async def process_email(bot, email):
    """Zpracuje jeden email: klasifikace → generování → potvrzení → odeslání."""
    logger.info(f"Zpracovávám: '{email['subject']}' od {email['from']}")

    # Označit hned — zabrání dvojímu zpracování i kdyby byl email v threadu s reply
    mark_as_processed(email["id"])

    email_type = classify_email(email)

    if email_type == UNKNOWN_TYPE:
        logger.info("Neznámý typ — přeskakuji.")
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
        return

    if email_type == ESCALATION_TYPE:
        logger.info("Eskalace — notifikuji člověka.")
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
        mark_as_processed(email["id"])
        return

    if email_type not in AUTO_REPLY_TYPES:
        logger.info(f"Neznámý typ '{email_type}' — přeskakuji.")
        mark_as_processed(email["id"])
        return

    draft = generate_reply(email, email_type)

    if DRY_RUN:
        logger.info(f"[DRY RUN] Draft odpovědi:\n{draft}\n---")
        mark_as_processed(email["id"])
        return

    await send_approval_request(bot, email, email_type, draft)
    approved = await wait_for_approval(bot)

    if approved is None:
        # Timeout — email zůstane nezpracovaný, zpracuje se při příštím /check
        logger.info("Timeout — email vrácen do fronty.")
        return
    elif approved:
        await bot.send_message(
            chat_id=os.getenv("TELEGRAM_CHAT_ID"),
            text="👍 Odesílám..."
        )
        send_reply(email, draft)
        logger.info("Email odeslán.")
        await bot.send_message(
            chat_id=os.getenv("TELEGRAM_CHAT_ID"),
            text="✅ Email byl odeslán."
        )
    else:
        logger.info("Email zamítnut.")
        await bot.send_message(
            chat_id=os.getenv("TELEGRAM_CHAT_ID"),
            text="❌ Email přeskočen."
        )

    mark_as_processed(email["id"])


async def run_check(bot):
    """Zkontroluje nové emaily. Používá zámek aby nešly dva checy najednou."""
    async with _check_lock:
        logger.info("Spouštím check nových emailů...")
        emails = get_unprocessed_emails()

        if not emails:
            logger.info("Žádné nové emaily.")
            await bot.send_message(
                chat_id=os.getenv("TELEGRAM_CHAT_ID"),
                text="📭 Žádné nové emaily."
            )
            return

        for email in emails:
            try:
                await process_email(bot, email)
            except Exception as e:
                logger.error(f"Chyba při zpracování emailu {email['id']}: {e}", exc_info=True)


# --- Telegram command handlery ---

async def cmd_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/check — okamžitý check emailů."""
    await update.message.reply_text("🔍 Spouštím check emailů...")
    asyncio.create_task(run_check(context.bot))


async def cmd_yes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/yes — schválí čekající odpověď."""
    await resolve_approval(True)


async def cmd_no(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/no — zamítne čekající odpověď."""
    await resolve_approval(False)
    await update.message.reply_text("👎 Přeskočeno.")


async def scheduled_check(context: ContextTypes.DEFAULT_TYPE):
    """Automatický check spouštěný JobQueue."""
    await run_check(context.bot)


async def send_startup_message(context: ContextTypes.DEFAULT_TYPE):
    """Pošle uvítací zprávu při startu agenta."""
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    mode = "🔇 DRY RUN" if DRY_RUN else "🟢 PRODUKCE"
    text = (
        f"🤖 E-mailový agent spuštěn — {mode}\n"
        f"📧 {MAIL_ADDRESS} ({MAIL_CLIENT})\n"
        f"⏱ Check každých {CHECK_INTERVAL // 60} min\n\n"
        f"Zpracovávám:\n"
        f"  A1 stav objednávky\n"
        f"  A2 vrácení zboží\n"
        f"  A3 reklamace (klidná)\n"
        f"  B1 dotaz na produkt\n"
        f"  B2 odborný/zdravotní dotaz\n\n"
        f"  🚨 ESC → notifikace, bez auto-reply\n"
        f"  ⚪ UNK → zalogováno, bez akce\n\n"
        f"Příkazy: /check · /yes · /no"
    )
    await context.bot.send_message(chat_id=chat_id, text=text)


# --- Start ---

def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("check", cmd_check))
    app.add_handler(CommandHandler("yes", cmd_yes))
    app.add_handler(CommandHandler("no", cmd_no))

    # Uvítací zpráva při startu
    app.job_queue.run_once(send_startup_message, when=5)

    # Plánovaný check každých N minut
    app.job_queue.run_repeating(scheduled_check, interval=CHECK_INTERVAL, first=10)

    logger.info(f"Agent spuštěn. Interval: {CHECK_INTERVAL // 60} min. DRY_RUN={DRY_RUN}")
    logger.info("Příkazy: /check, /yes, /no")

    app.run_polling()


if __name__ == "__main__":
    main()
