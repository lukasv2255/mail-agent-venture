"""
Modul: Newsletter — týdenní real estate lead newsletter pro Moravu.

Aktivace: MODULE_NEWSLETTER=true

Rozhraní:
  setup(app)       — registruje /newsletter command + weekly job (pondělí 7:00)
  run_check(bot)   — ignoruje (newsletter má vlastní scheduling, nereaguje na /check)

Odesílatel i příjemce = klientova adresa (posílá sám sobě).
Formát newsletteru je v prompts/newsletter_format.md.

Env proměnné:
  NEWSLETTER_HOUR     — hodina odeslání v pondělí (default: 7)
  OPENAI_API_KEY      — povinné pro generování obsahu
  MAIL_CLIENT         — gmail nebo imap (default: gmail)
  GMAIL_ADDRESS       — pro Gmail
  IMAP_USER / SMTP_HOST / IMAP_PASSWORD — pro IMAP/SMTP
"""
import asyncio
import base64
import datetime
import logging
import os
import smtplib
from email.mime.text import MIMEText

import requests
from bs4 import BeautifulSoup
from ddgs import DDGS
from openai import OpenAI
from telegram.ext import CommandHandler

from src.gmail_client import get_gmail_service

logger = logging.getLogger(__name__)

NEWSLETTER_HOUR = int(os.getenv("NEWSLETTER_HOUR", "7"))
NEWSLETTER_MINUTE = int(os.getenv("NEWSLETTER_MINUTE", "0"))
NEWSLETTER_DAY = int(os.getenv("NEWSLETTER_DAY", "0"))       # 0=pondělí, 6=neděle (ignoruje se při INTERVAL_DAYS=1)
NEWSLETTER_INTERVAL_DAYS = int(os.getenv("NEWSLETTER_INTERVAL_DAYS", "7"))  # 1=denně, 7=týdně
COLLECT_TIMEOUT_SECONDS = int(os.getenv("NEWSLETTER_COLLECT_TIMEOUT_SECONDS", "120"))
GENERATE_TIMEOUT_SECONDS = int(os.getenv("NEWSLETTER_GENERATE_TIMEOUT_SECONDS", "180"))
SEND_TIMEOUT_SECONDS = int(os.getenv("NEWSLETTER_SEND_TIMEOUT_SECONDS", "45"))

_QUERIES_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "prompts", "newsletter_queries.txt")

# Max počet URL jejichž obsah plně stáhneme (pomalejší, ale lepší data)
MAX_FULL_SCRAPE = 3

_HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

_FORMAT_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "prompts", "newsletter_format.md")

_USER_PROMPT = """\
Dnešní datum: {date}
Týden: {week}/{year}

Data z průzkumu realitního trhu na Moravě:

--- DATA ---
{data}
--- KONEC ---

Sestav newsletter PŘESNĚ podle zadaného formátu. \
Filtruj jen to, co má přímý obchodní potenciál pro prodejce balkonů.
"""


def _load_format() -> str:
    path = os.path.normpath(_FORMAT_FILE)
    with open(path, encoding="utf-8") as f:
        return f.read()


def _load_queries() -> list[str]:
    path = os.path.normpath(_QUERIES_FILE)
    with open(path, encoding="utf-8") as f:
        return [
            line.strip()
            for line in f
            if line.strip() and not line.startswith("#")
        ]


def setup(app):
    app.add_handler(CommandHandler("newsletter", _cmd_newsletter))

    now = datetime.datetime.utcnow()  # APScheduler pracuje v UTC
    send_time = datetime.time(hour=NEWSLETTER_HOUR, minute=NEWSLETTER_MINUTE)
    first_run = datetime.datetime.combine(now.date(), send_time)
    if first_run <= now:
        # Dnes UTC už bylo — příště v nastavený den (NEWSLETTER_DAY)
        days_ahead = (NEWSLETTER_DAY - now.weekday()) % 7 or 7
        first_run = datetime.datetime.combine(
            now.date() + datetime.timedelta(days=days_ahead),
            send_time,
        )

    # Sekundy od teď UTC — timezone-safe
    seconds_until = max(1, (first_run - now).total_seconds())

    app.job_queue.run_repeating(
        _scheduled_newsletter,
        interval=datetime.timedelta(days=NEWSLETTER_INTERVAL_DAYS),
        first=seconds_until,
        name="newsletter_weekly",
    )
    logger.info(f"Modul newsletter: inicializován. První odeslání: {first_run:%Y-%m-%d %H:%M} (za {seconds_until:.0f}s), interval: {NEWSLETTER_INTERVAL_DAYS}d")


async def run_check(bot):
    pass  # Newsletter má vlastní scheduling — nereaguje na /check


async def _cmd_newsletter(update, context):
    """/newsletter — okamžité vygenerování a odeslání."""
    await update.message.reply_text("📬 Generuji newsletter... (1–2 min)")
    asyncio.create_task(_generate_and_send(context.bot))


async def _scheduled_newsletter(context):
    await _generate_and_send(context.bot)


async def _generate_and_send(bot):
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    try:
        loop = asyncio.get_event_loop()

        logger.info("[newsletter] Sbírám data z webu...")
        await bot.send_message(chat_id=chat_id, text="🔎 Newsletter: sbírám data z webu...")
        raw_data = await asyncio.wait_for(
            loop.run_in_executor(None, _collect_data),
            timeout=COLLECT_TIMEOUT_SECONDS,
        )

        logger.info("[newsletter] Generuji obsah pomocí GPT-4o...")
        await bot.send_message(chat_id=chat_id, text="🧠 Newsletter: generuji obsah...")
        content = await asyncio.wait_for(
            loop.run_in_executor(None, _generate_content, raw_data),
            timeout=GENERATE_TIMEOUT_SECONDS,
        )

        logger.info("[newsletter] Odesílám email...")
        await bot.send_message(chat_id=chat_id, text="📤 Newsletter: odesílám email...")
        recipient = await asyncio.wait_for(
            loop.run_in_executor(None, _send_email, content),
            timeout=SEND_TIMEOUT_SECONDS,
        )

        await bot.send_message(chat_id=chat_id, text=f"✅ Newsletter odeslán na {recipient}")
        logger.info(f"[newsletter] Hotovo → {recipient}")

    except asyncio.TimeoutError as e:
        logger.error("[newsletter] Timeout při zpracování newsletteru.", exc_info=True)
        await bot.send_message(chat_id=chat_id, text="❌ Newsletter selhal: timeout při zpracování.")
        raise e
    except Exception as e:
        logger.error(f"[newsletter] Chyba: {e}", exc_info=True)
        await bot.send_message(chat_id=chat_id, text=f"❌ Newsletter selhal: {e}")


# ---------------------------------------------------------------------------
# Sběr dat
# ---------------------------------------------------------------------------

def _collect_data() -> str:
    """
    Prohledá DuckDuckGo pro každý dotaz.
    Pro top výsledky navíc stáhne obsah celé stránky (lepší data pro GPT).
    """
    sections = []
    scraped_urls: set[str] = set()
    full_scrape_count = 0

    for query in _load_queries():
        try:
            results = _ddg_search(query)
            if not results:
                continue

            lines = []
            for item in results:
                url = item["url"]
                lines.append(
                    f"TITULEK: {item['title']}\n"
                    f"URL: {url}\n"
                    f"POPIS: {item['snippet']}"
                )
                # Stáhnout plný obsah pro první výsledky každého dotazu
                if (
                    full_scrape_count < MAX_FULL_SCRAPE
                    and url not in scraped_urls
                    and url.startswith("http")
                ):
                    text = _fetch_page_text(url)
                    if text:
                        lines.append(f"OBSAH STRÁNKY:\n{text}")
                        scraped_urls.add(url)
                        full_scrape_count += 1

            sections.append(f"=== {query} ===\n" + "\n\n".join(lines))
            logger.info(f"[newsletter] '{query[:45]}': {len(results)} výsledků")

        except Exception as e:
            logger.warning(f"[newsletter] Chyba při dotazu '{query}': {e}")

    return "\n\n".join(sections) or "Žádná data se nepodařilo získat."


def _ddg_search(query: str, n: int = 4) -> list[dict]:
    """Vrátí seznam {title, url, snippet} přes ddgs knihovnu. Retry 3x při chybě."""
    for attempt in range(3):
        try:
            with DDGS(verify=False) as ddgs:
                raw = ddgs.text(query, region="cz-cs", max_results=n)
                return [
                    {"title": r["title"], "url": r["href"], "snippet": r["body"]}
                    for r in (raw or [])
                ]
        except Exception as e:
            if attempt == 2:
                raise
            logger.debug(f"[newsletter] ddgs pokus {attempt + 1} selhal: {e}, zkouším znovu...")
            import time
            time.sleep(2)
    return []


def _fetch_page_text(url: str, max_chars: int = 2000) -> str:
    """Stáhne stránku a vrátí čistý text (bez HTML tagů, max max_chars znaků)."""
    try:
        resp = requests.get(url, headers=_HTTP_HEADERS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        # Odstraň navigaci, skripty, styly
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        # Zkrať přebytečné mezery
        import re
        text = re.sub(r"\s{2,}", " ", text)
        return text[:max_chars]
    except Exception as e:
        logger.debug(f"[newsletter] Nelze načíst {url}: {e}")
        return ""


# ---------------------------------------------------------------------------
# Generování obsahu
# ---------------------------------------------------------------------------

def _generate_content(raw_data: str) -> str:
    """Odešle data do GPT-4o, vrátí hotový text newsletteru."""
    today = datetime.date.today()
    week = today.isocalendar()[1]
    year = today.year

    format_instructions = _load_format()
    system = (
        "Jsi expert na realitní trh v ČR se zaměřením na Moravu.\n\n"
        "INSTRUKCE A FORMÁT NEWSLETTERU:\n"
        + format_instructions
    )
    user_msg = _USER_PROMPT.format(
        date=today.strftime("%d. %m. %Y"),
        week=week,
        year=year,
        data=raw_data,
    )

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.3,
        max_tokens=3000,
        timeout=GENERATE_TIMEOUT_SECONDS,
    )
    return response.choices[0].message.content


# ---------------------------------------------------------------------------
# Odeslání emailu
# ---------------------------------------------------------------------------

def _send_email(content: str) -> str:
    """Odešle newsletter. Odesílatel = příjemce (klient posílá sám sobě)."""
    mail_client = os.getenv(
        "NEWSLETTER_MAIL_CLIENT",
        os.getenv("MAIL_CLIENT", "gmail"),
    ).lower()
    today = datetime.date.today()
    week = today.isocalendar()[1]
    subject = f"📬 REALITY INFO – MORAVA | Týden {week}/{today.year}"

    if mail_client == "gmail":
        return _send_via_gmail(content, subject)
    return _send_via_smtp(content, subject)


def _send_via_gmail(content: str, subject: str) -> str:
    sender_address = os.getenv("GMAIL_ADDRESS")
    recipient_address = os.getenv("NEWSLETTER_RECIPIENT_EMAIL", os.getenv("GMAIL_ADDRESS"))
    if not sender_address:
        raise ValueError("GMAIL_ADDRESS není nastavena.")
    if not recipient_address:
        raise ValueError("NEWSLETTER_RECIPIENT_EMAIL ani GMAIL_ADDRESS není nastavena.")

    service = get_gmail_service()
    msg = MIMEText(content, "plain", "utf-8")
    msg["To"] = recipient_address
    msg["Subject"] = subject
    # From nastavuje Gmail sám — nenastavovat ručně (viz lessons.md)

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    service.users().messages().send(userId="me", body={"raw": raw}).execute()
    return recipient_address


def _send_via_smtp(content: str, subject: str) -> str:
    address = os.getenv("NEWSLETTER_RECIPIENT_EMAIL", os.getenv("IMAP_USER"))
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    password = os.getenv("IMAP_PASSWORD")

    if not all([address, smtp_host, password]):
        raise ValueError("Pro SMTP nastav NEWSLETTER_RECIPIENT_EMAIL nebo IMAP_USER, SMTP_HOST, IMAP_PASSWORD.")

    msg = MIMEText(content, "plain", "utf-8")
    msg["To"] = address
    msg["From"] = address
    msg["Subject"] = subject

    with smtplib.SMTP(smtp_host, smtp_port, timeout=SEND_TIMEOUT_SECONDS) as server:
        server.starttls()
        server.login(address, password)
        server.send_message(msg)

    return address
