"""
Modul: Sorter — real-time třídění inboxu přes IMAP IDLE.

Server pushne notifikaci ihned když přijde nový mail.
Sorter ho okamžitě klasifikuje a přesune do cílové složky (nebo ponechá).

Aktivace: MODULE_SORTER=true

Env proměnné:
  SORTER_TARGET_FOLDER   Složka pro nerelevantní emaily (výchozí: "others")
  SORTER_MANUAL_LIMIT    Max počet emailů pro /sort (výchozí: 200)
  IMAP_HOST, IMAP_PORT, IMAP_USER, IMAP_PASSWORD

Rozhraní:
  setup(app)      — spustí IDLE listener jako asyncio task na pozadí
  run_check(bot)  — jednorázový průchod inboxem (pro /check příkaz)
"""
import asyncio
import email as email_lib
import email.header
import email.utils
import hashlib
import json
import logging
import os
import threading
from datetime import datetime, timezone

from imapclient import IMAPClient
from openai import OpenAI
from telegram.ext import CommandHandler

logger = logging.getLogger(__name__)

IMAP_HOST = os.getenv("IMAP_HOST", "")
IMAP_PORT = int(os.getenv("IMAP_PORT", "993"))
IMAP_USER = os.getenv("IMAP_USER", "")
IMAP_PASSWORD = os.getenv("IMAP_PASSWORD", "")
TARGET_FOLDER = os.getenv("SORTER_TARGET_FOLDER", "others")
MANUAL_SORT_LIMIT = int(os.getenv("SORTER_MANUAL_LIMIT", "200"))
GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS", "")

NEWSLETTER_HEADERS = ("List-Unsubscribe", "List-ID", "List-Post")

CLASSIFIER_PROMPT = """Jsi asistent třídící e-maily.

Odpověz POUZE slovem KEEP nebo MOVE.

KEEP = e-mail je osobní obchodní nabídka nebo poptávka služeb adresovaná přímo příjemci
       (např. nabídka spolupráce, B2B poptávka, žádost o schůzku nebo call)

MOVE = vše ostatní: newslettery, hromadné emaily, marketingové nabídky, novinky,
       automatické zprávy, spam, soukromé emaily, faktury, systémové notifikace

Odpověz pouze: KEEP nebo MOVE"""

HISTORY_FILE = "logs/sorter/sorter.jsonl"

_ai_client = None
_bot = None  # uložíme při setup pro případné budoucí Telegram notifikace
_process_lock = threading.Lock()


def _semantic_key(sender: str, subject: str, body: str) -> str:
    value = "\n".join([
        sender.strip().lower(),
        subject.strip().lower(),
        (body or "")[:500].strip().lower(),
    ])
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _message_key(msg, raw: bytes) -> tuple[str, str]:
    message_id = (msg.get("Message-ID") or "").strip()
    if message_id:
        return message_id, message_id
    return "", hashlib.sha256(raw).hexdigest()


def _load_logged_sort_keys() -> tuple[set[str], set[str]]:
    logged_sort_keys = set()
    logged_sort_semantic_keys = set()
    if not os.path.exists(HISTORY_FILE):
        return logged_sort_keys, logged_sort_semantic_keys

    with open(HISTORY_FILE, encoding="utf-8") as f:
        for line in f:
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue

            if record.get("email_key"):
                logged_sort_keys.add(record["email_key"])
            logged_sort_semantic_keys.add(_semantic_key(
                record.get("from", ""),
                record.get("subject", ""),
                record.get("body", ""),
            ))
    return logged_sort_keys, logged_sort_semantic_keys


def _log_sort(sender: str, subject: str, body: str, decision: str, method: str, message_id: str, email_key: str):
    """Uloží výsledek třídění do logs/sorter/sorter.jsonl."""
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    logged_sort_keys, logged_sort_semantic_keys = _load_logged_sort_keys()
    semantic_key = _semantic_key(sender, subject, body)
    if email_key in logged_sort_keys or semantic_key in logged_sort_semantic_keys:
        return

    record = {
        "time": datetime.now(timezone.utc).isoformat(),
        "message_id": message_id,
        "email_key": email_key,
        "semantic_key": semantic_key,
        "from": sender,
        "subject": subject,
        "body": body,
        "decision": decision,   # KEEP / MOVE
        "method": method,       # ai / headers / self
        "outcome": "kept" if decision == "KEEP" else "moved",
    }
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


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


def _extract_addresses(value: str) -> set[str]:
    return {
        address.strip().lower()
        for _, address in email.utils.getaddresses([value or ""])
        if address and address.strip()
    }


def _is_internal_mail(msg) -> bool:
    sender_addresses = _extract_addresses(msg.get("From", ""))

    trusted_senders = {
        address.strip().lower()
        for address in (IMAP_USER, GMAIL_ADDRESS)
        if address and address.strip()
    }
    return bool(sender_addresses & trusted_senders)


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


def _empty_stats() -> dict:
    return {"checked": 0, "kept": 0, "moved": 0, "skipped": 0, "errors": 0}


def _process_uids(conn: IMAPClient, uids: list[int], label: str) -> dict:
    """Zpracuje zadané UID seznamy bez změny seen/unseen příznaků."""
    stats = _empty_stats()
    stats["checked"] = len(uids)
    if not uids:
        return stats

    logged_sort_keys, logged_sort_semantic_keys = _load_logged_sort_keys()
    messages = conn.fetch(uids, ["BODY.PEEK[]"])

    for uid, data in messages.items():
        try:
            raw = data[b"BODY[]"]
            msg = email_lib.message_from_bytes(raw)

            subject = _decode_header(msg.get("Subject", "(bez předmětu)"))
            sender = _decode_header(msg.get("From", ""))
            message_id, email_key = _message_key(msg, raw)
            if email_key in logged_sort_keys:
                stats["skipped"] += 1
                continue

            # Interní e-maily od vlastních agent účtů nikdy nepřesouvat.
            if _is_internal_mail(msg):
                logger.info(f"[sorter] KEEP/internal | {sender} | {subject}")
                _log_sort(sender, subject, "", "KEEP", "internal", message_id, email_key)
                stats["kept"] += 1
                continue

            if _is_newsletter(msg):
                logger.info(f"[sorter] MOVE/hlavičky | {sender} | {subject}")
                conn.move([uid], TARGET_FOLDER)
                _log_sort(sender, subject, "", "MOVE", "headers", message_id, email_key)
                stats["moved"] += 1
                continue

            body = _extract_body(msg)
            if _semantic_key(sender, subject, body) in logged_sort_semantic_keys:
                stats["skipped"] += 1
                continue

            decision = _classify_with_ai(subject, sender, body)

            if decision == "KEEP":
                logger.info(f"[sorter] KEEP          | {sender} | {subject}")
                stats["kept"] += 1
            else:
                logger.info(f"[sorter] MOVE/AI       | {sender} | {subject}")
                conn.move([uid], TARGET_FOLDER)
                stats["moved"] += 1
            _log_sort(sender, subject, body, decision, "ai", message_id, email_key)
        except Exception as e:
            stats["errors"] += 1
            logger.error(f"[sorter] Chyba při zpracování UID {uid} ({label}): {e}", exc_info=True)

    return stats


def _process_unseen(conn: IMAPClient) -> dict:
    """Zpracuje všechny nepřečtené emaily v inboxu."""
    with _process_lock:
        conn.select_folder("INBOX")
        uids = conn.search(["UNSEEN"])
        if not uids:
            return _empty_stats()

        logger.info(f"[sorter] Zpracovávám {len(uids)} nových emailů...")
        return _process_uids(conn, uids, "unseen")


def _process_inbox(limit: int = MANUAL_SORT_LIMIT) -> dict:
    """Ruční třídění existujícího inboxu pro /sort. Nemění seen/unseen stav."""
    with _process_lock:
        conn = _connect()
        try:
            conn.select_folder("INBOX")
            uids = conn.search(["ALL"])
            if limit > 0:
                uids = list(uids)[-limit:]
            logger.info(f"[sorter] /sort zpracovává {len(uids)} emailů z INBOXu...")
            return _process_uids(conn, uids, "manual")
        finally:
            conn.logout()


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
    app.add_handler(CommandHandler("sort", _cmd_sort))
    asyncio.get_event_loop().create_task(_idle_loop())
    logger.info(f"[sorter] IDLE listener spuštěn. Cílová složka: '{TARGET_FOLDER}'")


async def run_check(bot):
    """Jednorázový průchod inboxem — pro /check příkaz."""
    loop = asyncio.get_event_loop()
    conn = await loop.run_in_executor(None, _connect)
    try:
        await loop.run_in_executor(None, _process_unseen, conn)
    finally:
        conn.logout()


async def _cmd_sort(update, context):
    """/sort — ručně setřídí existující INBOX bez změny seen/unseen."""
    limit = MANUAL_SORT_LIMIT
    if context.args:
        try:
            limit = max(1, int(context.args[0]))
        except ValueError:
            await update.message.reply_text("Použití: /sort nebo /sort 500")
            return

    await update.message.reply_text(
        f"🗂 Spouštím třídění INBOXu. Limit: {limit} emailů.\n"
        "Stav přečteno/nepřečteno neměním."
    )

    loop = asyncio.get_event_loop()
    try:
        stats = await loop.run_in_executor(None, _process_inbox, limit)
        await update.message.reply_text(
            "✅ /sort hotovo\n"
            f"Zkontrolováno: {stats['checked']}\n"
            f"Ponecháno: {stats['kept']}\n"
            f"Přesunuto: {stats['moved']}\n"
            f"Přeskočeno: {stats['skipped']}\n"
            f"Chyby: {stats['errors']}"
        )
    except Exception as e:
        logger.error(f"[sorter] /sort selhal: {e}", exc_info=True)
        await update.message.reply_text(f"❌ /sort selhal: {e}")
