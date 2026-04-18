"""
Modul: Sorter — real-time třídění inboxu přes IMAP IDLE.

Server pushne notifikaci ihned když přijde nový mail.
Sorter ho okamžitě klasifikuje a přesune do cílové složky (nebo ponechá).

Aktivace: MODULE_SORTER=true

Env proměnné:
  SORTER_TARGET_FOLDER   Složka pro nerelevantní emaily (výchozí: "others")
  IMAP_HOST, IMAP_PORT, IMAP_USER, IMAP_PASSWORD

Rozhraní:
  setup(app)      — spustí IDLE listener jako asyncio task na pozadí
  run_check(bot)  — jednorázový průchod inboxem (pro /check příkaz)
"""
import asyncio
import email as email_lib
import email.header
import logging
import os

from imapclient import IMAPClient
from openai import OpenAI

logger = logging.getLogger(__name__)

IMAP_HOST = os.getenv("IMAP_HOST", "")
IMAP_PORT = int(os.getenv("IMAP_PORT", "993"))
IMAP_USER = os.getenv("IMAP_USER", "")
IMAP_PASSWORD = os.getenv("IMAP_PASSWORD", "")
TARGET_FOLDER = os.getenv("SORTER_TARGET_FOLDER", "others")

NEWSLETTER_HEADERS = ("List-Unsubscribe", "List-ID", "List-Post")

CLASSIFIER_PROMPT = """Jsi asistent třídící e-maily.

Odpověz POUZE slovem KEEP nebo MOVE.

KEEP = e-mail je osobní obchodní nabídka nebo poptávka služeb adresovaná přímo příjemci
       (např. nabídka spolupráce, B2B poptávka, žádost o schůzku nebo call)

MOVE = vše ostatní: newslettery, hromadné emaily, marketingové nabídky, novinky,
       automatické zprávy, spam, soukromé emaily, faktury, systémové notifikace

Odpověz pouze: KEEP nebo MOVE"""

_ai_client = None
_bot = None  # uložíme při setup pro případné budoucí Telegram notifikace


def _get_ai_client():
    global _ai_client
    if _ai_client is None:
        _ai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _ai_client


def _connect() -> IMAPClient:
    conn = IMAPClient(IMAP_HOST, port=IMAP_PORT, ssl=True)
    conn.login(IMAP_USER, IMAP_PASSWORD)
    return conn


def _decode_header(value: str) -> str:
    parts = email.header.decode_header(value or "")
    decoded = []
    for part, charset in parts:
        if isinstance(part, bytes):
            decoded.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            decoded.append(part)
    return " ".join(decoded)


def _extract_body(msg) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    return payload.decode("utf-8", errors="replace")
    payload = msg.get_payload(decode=True)
    if payload:
        return payload.decode("utf-8", errors="replace")
    return ""


def _is_newsletter(msg) -> bool:
    for header in NEWSLETTER_HEADERS:
        if msg.get(header):
            return True
    precedence = (msg.get("Precedence") or "").lower()
    return precedence in ("bulk", "list", "junk")


def _classify_with_ai(subject: str, sender: str, body: str) -> str:
    user_message = f"Od: {sender}\nPředmět: {subject}\n\n{body[:1500]}"
    response = _get_ai_client().chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=5,
        messages=[
            {"role": "system", "content": CLASSIFIER_PROMPT},
            {"role": "user", "content": user_message},
        ],
    )
    result = response.choices[0].message.content.strip().upper()
    return "KEEP" if result.startswith("KEEP") else "MOVE"


def _process_unseen(conn: IMAPClient):
    """Zpracuje všechny nepřečtené emaily v inboxu."""
    conn.select_folder("INBOX")
    uids = conn.search(["UNSEEN"])
    if not uids:
        return

    logger.info(f"[sorter] Zpracovávám {len(uids)} nových emailů...")
    messages = conn.fetch(uids, ["RFC822"])

    for uid, data in messages.items():
        raw = data[b"RFC822"]
        msg = email_lib.message_from_bytes(raw)

        subject = _decode_header(msg.get("Subject", "(bez předmětu)"))
        sender = _decode_header(msg.get("From", ""))

        # Emaily od sebe sama vždy ponechat (vlastní newslettery apod.)
        if IMAP_USER and IMAP_USER.lower() in sender.lower():
            logger.info(f"[sorter] KEEP/self     | {sender} | {subject}")
            continue

        if _is_newsletter(msg):
            logger.info(f"[sorter] MOVE/hlavičky | {sender} | {subject}")
            conn.move([uid], TARGET_FOLDER)
            continue

        body = _extract_body(msg)
        decision = _classify_with_ai(subject, sender, body)

        if decision == "KEEP":
            logger.info(f"[sorter] KEEP          | {sender} | {subject}")
        else:
            logger.info(f"[sorter] MOVE/AI       | {sender} | {subject}")
            conn.move([uid], TARGET_FOLDER)


POLL_INTERVAL = int(os.getenv("SORTER_POLL_INTERVAL", "60"))  # sekund


async def _idle_loop():
    """
    Běží na pozadí celou dobu.
    Zkouší IDLE — pokud server nepodporuje, fallback na polling každých POLL_INTERVAL sekund.
    Při výpadku se reconnectuje automaticky.
    """
    while True:
        try:
            conn = _connect()

            # Zpracuj emaily které přišly když agent nebyl připojený
            _process_unseen(conn)

            # Zkus IDLE
            try:
                conn.select_folder("INBOX")
                conn.idle()
                logger.info("[sorter] IDLE aktivní — čekám na push notifikace...")

                while True:
                    responses = await asyncio.get_event_loop().run_in_executor(
                        None, lambda: conn.idle_check(timeout=10 * 60)
                    )
                    conn.idle_done()
                    if responses:
                        _process_unseen(conn)
                    conn.idle()

            except Exception:
                # IDLE nepodporováno — fallback na polling
                logger.info(f"[sorter] IDLE nepodporováno, polling každých {POLL_INTERVAL}s...")
                conn.logout()
                while True:
                    await asyncio.sleep(POLL_INTERVAL)
                    try:
                        c = _connect()
                        _process_unseen(c)
                        c.logout()
                    except Exception as e:
                        logger.error(f"[sorter] Chyba při pollingu: {e}")

        except Exception as e:
            logger.error(f"[sorter] Chyba v sorter loop: {e} — restartuji za 30s...")
            await asyncio.sleep(30)


def setup(app):
    """Spustí IDLE listener jako asyncio task na pozadí."""
    global _bot
    _bot = app.bot
    asyncio.get_event_loop().create_task(_idle_loop())
    logger.info(f"[sorter] IDLE listener spuštěn. Cílová složka: '{TARGET_FOLDER}'")


async def run_check(bot):
    """Jednorázový průchod inboxem — pro /check příkaz."""
    conn = _connect()
    _process_unseen(conn)
    conn.logout()
