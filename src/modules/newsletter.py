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
  NEWSLETTER_INTERVAL_DAYS — interval odesílání v dnech (default: 1)
  NEWSLETTER_MIN_CHANGE — min. odlišnost vs. poslední (default: 0.12)
  NEWSLETTER_FORCE_SEND — vynutí odeslání i při podobnosti (default: false)
  OPENAI_API_KEY      — povinné pro generování obsahu
  MAIL_CLIENT         — gmail nebo imap (default: gmail)
  GMAIL_ADDRESS       — pro Gmail
  IMAP_USER / SMTP_HOST / IMAP_PASSWORD — pro IMAP/SMTP
"""
from __future__ import annotations

import asyncio
import base64
import datetime
import logging
import os
import json
import re
import smtplib
from email.mime.text import MIMEText
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from ddgs import DDGS
from openai import OpenAI
from telegram.ext import CommandHandler

from src.config import PROMPTS_DIR
from src.config import DATA_DIR
from src.gmail_client import get_gmail_service

logger = logging.getLogger(__name__)

NEWSLETTER_HOUR = int(os.getenv("NEWSLETTER_HOUR", "7"))
NEWSLETTER_MINUTE = int(os.getenv("NEWSLETTER_MINUTE", "0"))
NEWSLETTER_DAY = int(os.getenv("NEWSLETTER_DAY", "0"))       # 0=pondělí, 6=neděle (ignoruje se při INTERVAL_DAYS=1)
NEWSLETTER_INTERVAL_DAYS = int(os.getenv("NEWSLETTER_INTERVAL_DAYS", "1"))  # 1=denně, 7=týdně
NEWSLETTER_MIN_CHANGE = float(os.getenv("NEWSLETTER_MIN_CHANGE", "0.12"))  # min. odlišnost (0–1), jinak skip
NEWSLETTER_FORCE_SEND = os.getenv("NEWSLETTER_FORCE_SEND", "false").lower() in ("1", "true", "yes")

_QUERIES_FILE = PROMPTS_DIR / "newsletter_queries.txt"
_SOURCES_FILE = PROMPTS_DIR / "newsletter_sources.txt"

# Max počet URL jejichž obsah plně stáhneme (pomalejší, ale lepší data)
MAX_FULL_SCRAPE = 3

_HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

_FORMAT_FILE = PROMPTS_DIR / "newsletter_format.md"

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

_DOMAIN_STATS_FILE = DATA_DIR / "newsletter" / "domain_stats.json"
_LAST_SENT_FILE = DATA_DIR / "newsletter" / "last_sent.json"


def _load_format() -> str:
    with open(_FORMAT_FILE, encoding="utf-8") as f:
        return f.read()


def _load_queries() -> list[str]:
    with open(_QUERIES_FILE, encoding="utf-8") as f:
        return [
            line.strip()
            for line in f
            if line.strip() and not line.startswith("#")
        ]

def _load_sources() -> list[str]:
    """
    Volitelný whitelist domén. Když soubor neexistuje, vrátí prázdný list.
    """
    try:
        with open(_SOURCES_FILE, encoding="utf-8") as f:
            sources: list[str] = []
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                # normalizace: doména bez protokolu a bez cesty
                line = re.sub(r"^https?://", "", line)
                line = line.split("/")[0].strip()
                if line:
                    sources.append(line)
            return sources
    except FileNotFoundError:
        return []


def _extract_domain(url: str) -> str:
    try:
        parsed = urlparse(url)
        host = (parsed.netloc or "").lower()
        if host.startswith("www."):
            host = host[4:]
        return host
    except Exception:
        return ""


def _bump_domain_stats(urls: list[str]) -> None:
    """
    Ukládá agregované počty domén z výsledků vyhledávání.
    Best-effort: při chybě jen zaloguje debug a pokračuje.
    """
    try:
        counts: dict[str, int] = {}
        for url in urls:
            domain = _extract_domain(url)
            if not domain:
                continue
            counts[domain] = counts.get(domain, 0) + 1
        if not counts:
            return

        _DOMAIN_STATS_FILE.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(_DOMAIN_STATS_FILE, encoding="utf-8") as f:
                current = json.load(f) or {}
        except FileNotFoundError:
            current = {}
        except Exception:
            current = {}

        for domain, inc in counts.items():
            current[domain] = int(current.get(domain, 0)) + inc

        with open(_DOMAIN_STATS_FILE, "w", encoding="utf-8") as f:
            json.dump(current, f, ensure_ascii=False, indent=2, sort_keys=True)
    except Exception as e:
        logger.debug(f"[newsletter] Nelze uložit statistiky domén: {e}")


def _normalize_for_similarity(text: str) -> str:
    """
    Normalizace pro porovnání "podobnosti newsletteru".
    Cíl: ignorovat týden/datum a stabilizovat whitespace.
    """
    text = (text or "").strip().lower()
    if not text:
        return ""
    # Zahodit variabilní hlavičku s týdnem (pokud existuje)
    text = re.sub(r"týden\s+\d+\s*/\s*\d{4}", "týden X / YYYY", text, flags=re.IGNORECASE)
    text = re.sub(r"\b\d{1,2}\.\s*\d{1,2}\.\s*\d{4}\b", "DD. MM. YYYY", text)
    # Unifikace separatorů
    text = text.replace("───────────────────────────────", "—")
    # Smazat opakované mezery
    text = re.sub(r"\s+", " ", text)
    return text


def _shingles(text: str, k: int = 7) -> set[str]:
    text = _normalize_for_similarity(text)
    if len(text) <= k:
        return {text} if text else set()
    return {text[i : i + k] for i in range(0, len(text) - k + 1)}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def _load_last_sent() -> dict:
    try:
        with open(_LAST_SENT_FILE, encoding="utf-8") as f:
            return json.load(f) or {}
    except FileNotFoundError:
        return {}
    except Exception as e:
        logger.debug(f"[newsletter] Nelze načíst last_sent: {e}")
        return {}


def _save_last_sent(content: str, recipient: str, subject: str) -> None:
    try:
        _LAST_SENT_FILE.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "sent_at": datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "recipient": recipient,
            "subject": subject,
            "content": content,
        }
        with open(_LAST_SENT_FILE, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.debug(f"[newsletter] Nelze uložit last_sent: {e}")


def _should_send(new_content: str) -> tuple[bool, float]:
    """
    Vrátí (poslat?, odlišnost). Odlišnost = 1 - podobnost.
    """
    last = _load_last_sent()
    old_content = (last.get("content") or "").strip()
    if not old_content:
        return True, 1.0

    sim = _jaccard(_shingles(old_content), _shingles(new_content))
    change = 1.0 - sim
    return change >= NEWSLETTER_MIN_CHANGE, change


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
        raw_data = await loop.run_in_executor(None, _collect_data)

        logger.info("[newsletter] Generuji obsah pomocí GPT-4o...")
        content = await loop.run_in_executor(None, _generate_content, raw_data)

        should_send, change = await loop.run_in_executor(None, _should_send, content)
        if NEWSLETTER_FORCE_SEND:
            should_send = True

        if not should_send:
            msg = f"⏭️ Newsletter neodeslán (příliš podobný poslednímu; změna {change:.0%})."
            await bot.send_message(chat_id=chat_id, text=msg)
            logger.info(f"[newsletter] Skip send: change={change:.3f}")
            return

        logger.info("[newsletter] Odesílám email...")
        recipient, subject = await loop.run_in_executor(None, _send_email, content)
        await loop.run_in_executor(None, _save_last_sent, content, recipient, subject)

        await bot.send_message(chat_id=chat_id, text=f"✅ Newsletter odeslán na {recipient} (změna {change:.0%})")
        logger.info(f"[newsletter] Hotovo → {recipient}, change={change:.3f}")

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

    sources = _load_sources()
    source_queries: list[str] = []
    if sources:
        # 2 doplňkové dotazy na doménu: (A) lead signály, (B) inspirační témata
        for domain in sources[:30]:
            source_queries.append(
                f"site:{domain} (balkon OR balkón OR lodžie OR terasa) (developer OR projekt OR bytový dům OR rekonstrukce OR veřejná zakázka)"
            )
            source_queries.append(
                f"site:{domain} (balkon OR balkón OR lodžie OR terasa) (zábradlí OR zasklení OR hydroizolace OR statika OR koroze OR sanace)"
            )

    all_queries = _load_queries() + source_queries

    all_result_urls: list[str] = []
    for query in all_queries:
        try:
            results = _ddg_search(query)
            if not results:
                continue

            lines = []
            for item in results:
                url = item["url"]
                all_result_urls.append(url)
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

    _bump_domain_stats(all_result_urls)
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
        text = re.sub(r"\s{2,}", " ", text)
        return text[:max_chars]
    except Exception as e:
        logger.debug(f"[newsletter] Nelze načíst {url}: {e}")
        return ""


# ---------------------------------------------------------------------------
# Generování obsahu
# ---------------------------------------------------------------------------

def _generate_content(raw_data: str, today: datetime.date | None = None) -> str:
    """Odešle data do GPT-4o, vrátí hotový text newsletteru."""
    today = today or datetime.date.today()
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
    )
    return response.choices[0].message.content


# ---------------------------------------------------------------------------
# Odeslání emailu
# ---------------------------------------------------------------------------

def _send_email(content: str) -> tuple[str, str]:
    """Odešle newsletter. Odesílatel = příjemce (klient posílá sám sobě)."""
    mail_client = os.getenv("NEWSLETTER_MAIL_CLIENT", "gmail").lower()
    today = datetime.date.today()
    week = today.isocalendar()[1]
    subject = f"📬 REALITY INFO – MORAVA | Týden {week}/{today.year}"

    if mail_client == "gmail":
        recipient = _send_via_gmail(content, subject)
        return recipient, subject
    recipient = _send_via_smtp(content, subject)
    return recipient, subject


def _send_via_gmail(content: str, subject: str) -> str:
    address = os.getenv("GMAIL_ADDRESS")
    if not address:
        raise ValueError("GMAIL_ADDRESS není nastavena.")
    recipient = os.getenv("NEWSLETTER_RECIPIENT", address)

    service = get_gmail_service()
    msg = MIMEText(content, "plain", "utf-8")
    msg["To"] = recipient
    msg["Subject"] = subject
    # From nastavuje Gmail sám — nenastavovat ručně (viz lessons.md)

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    service.users().messages().send(userId="me", body={"raw": raw}).execute()
    return recipient


def _send_via_smtp(content: str, subject: str) -> str:
    address = os.getenv("IMAP_USER")
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    password = os.getenv("IMAP_PASSWORD")

    if not all([address, smtp_host, password]):
        raise ValueError("Pro SMTP nastav IMAP_USER, SMTP_HOST, IMAP_PASSWORD.")

    msg = MIMEText(content, "plain", "utf-8")
    msg["To"] = address
    msg["From"] = address
    msg["Subject"] = subject

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(address, password)
        server.send_message(msg)

    return address
