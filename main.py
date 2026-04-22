"""
E-mailový agent — hlavní vstupní bod.

Spuštění:
  python main.py

Aktivní moduly se konfigurují per-modul boolean proměnnými:
  MODULE_RESPONDER=true       # automatické odpovědi (výchozí: true)
  MODULE_SORTER=true          # třídění inboxu (výchozí: true)
  MODULE_NEWSLETTER=false     # tvorba newsletterů (výchozí: false)
"""
import asyncio
import importlib
import json
import logging
import os
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv()

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from src.mail_client import get_unprocessed_emails, mark_as_processed
from src.notifier import set_queue_remaining
from src.dashboard import start_dashboard, set_check_callback
from src.config import AGENT_ERR_LOG, AGENT_LOG, LOG_DIR, UPTIME_LOG

LOG_DIR.mkdir(parents=True, exist_ok=True)


def _log_uptime(event: str):
    record = {"time": datetime.now(timezone.utc).isoformat(), "event": event, "pid": os.getpid()}
    with open(UPTIME_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


_log_format = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

_agent_log_handler = logging.FileHandler(AGENT_LOG, encoding="utf-8")
_agent_log_handler.setLevel(logging.INFO)
_agent_log_handler.setFormatter(_log_format)

_agent_err_handler = logging.FileHandler(AGENT_ERR_LOG, encoding="utf-8")
_agent_err_handler.setLevel(logging.ERROR)
_agent_err_handler.setFormatter(_log_format)

logging.basicConfig(
    level=logging.INFO,
    handlers=[_agent_log_handler, _agent_err_handler],
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL_MINUTES", "60")) * 60

MAIL_CLIENT = os.getenv("MAIL_CLIENT", "gmail")
MAIL_ADDRESS = {
    "gmail": os.getenv("GMAIL_ADDRESS", "—"),
    "imap": os.getenv("IMAP_USER", "—"),
    "graph": os.getenv("GRAPH_USER_EMAIL", "—"),
    "helpdesk": os.getenv("HELPDESK_EMAIL", "—"),
}.get(MAIL_CLIENT, "—")

_check_lock = None


AVAILABLE_MODULES = ["responder", "sorter", "newsletter"]


def load_modules() -> list:
    """
    Načte aktivní moduly podle per-modul boolean env proměnných.

    MODULE_RESPONDER=true    # automatické odpovědi
    MODULE_SORTER=true       # třídění inboxu
    MODULE_NEWSLETTER=false  # tvorba newsletterů (výchozí: vypnuto)
    """
    modules = []
    for name in AVAILABLE_MODULES:
        env_key = f"MODULE_{name.upper()}"
        # responder a sorter zapnuty výchozně, newsletter vypnut
        default = "false" if name == "newsletter" else "true"
        enabled = os.getenv(env_key, default).lower() == "true"
        if not enabled:
            continue
        try:
            mod = importlib.import_module(f"src.modules.{name}")
            modules.append((name, mod))
            logger.info(f"Modul načten: {name}")
        except ImportError as e:
            logger.error(f"Nelze načíst modul '{name}': {e}")
    return modules


async def run_check(bot, modules: list):
    """
    Zkontroluje nové emaily a spustí každý aktivní modul.

    Moduly se dvěma možnými rozhraními:
      run_check(bot)    — modul má vlastní IMAP cyklus (např. sorter)
      run(bot, email)   — modul zpracovává emaily jeden po druhém (např. responder)
    """
    global _check_lock
    if _check_lock is None:
        _check_lock = asyncio.Lock()
    async with _check_lock:
        logger.info("Spouštím check...")

        # Moduly s vlastním cyklem (run_check)
        for name, mod in modules:
            if hasattr(mod, "run_check"):
                try:
                    await mod.run_check(bot)
                except Exception as e:
                    logger.error(f"Chyba v modulu '{name}' (run_check): {e}", exc_info=True)

        # Moduly zpracovávající emaily per-email (run)
        per_email_modules = [(name, mod) for name, mod in modules if hasattr(mod, "run") and not hasattr(mod, "run_check")]
        if not per_email_modules:
            return

        emails = get_unprocessed_emails()
        if not emails:
            logger.info("Žádné nové emaily.")
            await bot.send_message(
                chat_id=os.getenv("TELEGRAM_CHAT_ID"),
                text="📭 Žádné nové emaily."
            )
            return

        set_queue_remaining(len(emails))
        for name, mod in per_email_modules:
            try:
                if hasattr(mod, "run_batch"):
                    await mod.run_batch(bot, emails)
                else:
                    for i, email in enumerate(emails):
                        set_queue_remaining(len(emails) - i - 1)
                        await mod.run(bot, email)
            except Exception as e:
                logger.error(f"Chyba v modulu '{name}': {e}", exc_info=True)

        set_queue_remaining(0)


async def cmd_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/check — okamžitý check emailů."""
    await update.message.reply_text("🔍 Spouštím check emailů...")
    asyncio.create_task(run_check(context.bot, context.bot_data["modules"]))


async def scheduled_check(context: ContextTypes.DEFAULT_TYPE):
    """Automatický check spouštěný JobQueue."""
    await run_check(context.bot, context.bot_data["modules"])


async def send_startup_message(context: ContextTypes.DEFAULT_TYPE):
    """Pošle uvítací zprávu při startu agenta."""
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    modules = context.bot_data["modules"]
    module_names = ", ".join(name for name, _ in modules)
    has_responder = any(name == "responder" for name, _ in modules)
    has_sorter = any(name == "sorter" for name, _ in modules)
    has_newsletter = any(name == "newsletter" for name, _ in modules)
    cmds = ["/check"]
    if has_sorter:
        cmds.append("/sort")
    if has_responder:
        cmds += ["/yes", "/no"]
    if has_newsletter:
        cmds.append("/newsletter")
    text = (
        f"🤖 E-mailový agent spuštěn\n"
        f"📧 {MAIL_ADDRESS} ({MAIL_CLIENT})\n"
        f"⚙ Moduly: {module_names}\n"
        + (f"⏱ Check každých {CHECK_INTERVAL // 60} min\n" if has_responder else "")
        + f"\nPříkazy: {' '.join(cmds)}"
    )
    await context.bot.send_message(chat_id=chat_id, text=text)


def main():
    start_dashboard()

    token = os.getenv("TELEGRAM_BOT_TOKEN")

    modules = load_modules()

    async def post_init(application):
        # Zaregistruje callback až uvnitř správného event loop
        set_check_callback(lambda: run_check(application.bot, modules))

    app = Application.builder().token(token).post_init(post_init).build()

    app.bot_data["modules"] = modules

    # Každý modul zaregistruje své handlery
    for name, mod in modules:
        mod.setup(app)

    # Globální /check handler
    app.add_handler(CommandHandler("check", cmd_check))

    app.job_queue.run_once(send_startup_message, when=5)
    app.job_queue.run_repeating(scheduled_check, interval=CHECK_INTERVAL, first=10)

    logger.info(f"Agent spuštěn. Moduly: {[n for n, _ in modules]}. Interval: {CHECK_INTERVAL // 60} min.")
    _log_uptime("start")

    try:
        app.run_polling()
    finally:
        _log_uptime("stop")


if __name__ == "__main__":
    main()
