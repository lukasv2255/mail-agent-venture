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
import hashlib
import json
import logging
import os
import threading
from datetime import datetime, timezone
from typing import Optional

from imapclient import IMAPClient
from openai import OpenAI
from telegram.ext import CommandHandler

from src.config import SORTER_HISTORY_LOG, SORTER_STATE_FILE
from src.sorter_rules import add_move_rule_from_email, delete_move_rule, match_move_rule

logger = logging.getLogger(__name__)

IMAP_HOST = os.getenv("IMAP_HOST", "")
IMAP_PORT = int(os.getenv("IMAP_PORT", "993"))
IMAP_USER = os.getenv("IMAP_USER", "")
IMAP_PASSWORD = os.getenv("IMAP_PASSWORD", "")
TARGET_FOLDER = os.getenv("SORTER_TARGET_FOLDER", "others")
MANUAL_SORT_LIMIT = int(os.getenv("SORTER_MANUAL_LIMIT", "200"))
SORTER_HISTORY_MAX_ITEMS = int(os.getenv("SORTER_HISTORY_MAX_ITEMS", "10000"))

NEWSLETTER_HEADERS = ("List-Unsubscribe", "List-ID", "List-Post")

CLASSIFIER_PROMPT = """Jsi asistent třídící e-maily.

Odpověz POUZE slovem KEEP nebo MOVE.

KEEP = e-mail je osobní obchodní nabídka nebo poptávka služeb adresovaná přímo příjemci
       (např. nabídka spolupráce, B2B poptávka, žádost o schůzku nebo call)

MOVE = vše ostatní: newslettery, hromadné emaily, marketingové nabídky, novinky,
       automatické zprávy, spam, soukromé emaily, faktury, systémové notifikace

Odpověz pouze: KEEP nebo MOVE"""

HISTORY_FILE = SORTER_HISTORY_LOG
STATE_FILE = SORTER_STATE_FILE

_ai_client = None
_bot = None  # uložíme při setup pro případné budoucí Telegram notifikace
_process_lock = threading.Lock()
_startup_cursor_primed = False


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
    """
    Vrací dvě množiny klíčů:
    - moved_keys: email_key emailů s outcome='moved' — tyto přeskočíme (jsou ve spamu)
    - moved_semantic_keys: semantic_key emailů s outcome='moved' — přeskočíme i sémantické duplikáty

    Emaily s outcome='kept' záměrně NEpřeskakujeme, aby po vytvoření nového pravidla
    mohl sorter při dalším průchodu přesunout i dříve ponechané emaily.
    """
    moved_keys: set[str] = set()
    moved_semantic_keys: set[str] = set()
    if not HISTORY_FILE.exists():
        return moved_keys, moved_semantic_keys

    # Pro každý email_key chceme znát jeho aktuální outcome (poslední záznam vyhrává).
    latest: dict[str, dict] = {}
    with open(HISTORY_FILE, encoding="utf-8") as f:
        for line in f:
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            key = record.get("email_key")
            if key:
                latest[key] = record

    for record in latest.values():
        if record.get("outcome") == "moved":
            moved_keys.add(record["email_key"])
            moved_semantic_keys.add(_semantic_key(
                record.get("from", ""),
                record.get("subject", ""),
                record.get("body", ""),
            ))
    return moved_keys, moved_semantic_keys


def _load_state() -> dict:
    if not STATE_FILE.exists():
        return {}
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        logger.warning("[sorter] State file nelze načíst, obnovím ho při dalším průchodu.")
        return {}


def _save_state(state: dict):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False)


def _get_last_seen_uid() -> int:
    value = _load_state().get("last_seen_uid")
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _set_last_seen_uid(uid: int):
    current = _get_last_seen_uid()
    if uid <= current:
        return
    _save_state({
        "last_seen_uid": uid,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    })


def _get_highest_inbox_uid(conn: IMAPClient) -> int:
    conn.select_folder("INBOX")
    uids = conn.search(["ALL"])
    if not uids:
        return 0
    return max(int(uid) for uid in uids)


def _log_sort(
    sender: str,
    subject: str,
    body: str,
    decision: str,
    method: str,
    message_id: str,
    email_key: str,
    *,
    uid: str = "",
    folder: str = "INBOX",
    list_id: str = "",
    rule_type: str = "",
    rule_value: str = "",
    force: bool = False,
):
    """Uloží výsledek třídění do persistentní sorter historie."""
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    logged_sort_keys, logged_sort_semantic_keys = _load_logged_sort_keys()
    semantic_key = _semantic_key(sender, subject, body)
    if not force and (email_key in logged_sort_keys or semantic_key in logged_sort_semantic_keys):
        return

    record = {
        "time": datetime.now(timezone.utc).isoformat(),
        "uid": uid,
        "folder": folder,
        "message_id": message_id,
        "email_key": email_key,
        "semantic_key": semantic_key,
        "list_id": list_id,
        "from": sender,
        "subject": subject,
        "body": body,
        "body_display": body[:1000] if body else "",
        "decision": decision,   # KEEP / MOVE
        "method": method,       # ai / headers / self
        "rule_type": rule_type,
        "rule_value": rule_value,
        "outcome": "kept" if decision == "KEEP" else "moved",
    }
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    _trim_history_file()


def _trim_history_file():
    if SORTER_HISTORY_MAX_ITEMS <= 0 or not HISTORY_FILE.exists():
        return

    lines = HISTORY_FILE.read_text(encoding="utf-8").splitlines()
    overflow = len(lines) - SORTER_HISTORY_MAX_ITEMS
    if overflow <= 0:
        return

    HISTORY_FILE.write_text(
        "\n".join(lines[-SORTER_HISTORY_MAX_ITEMS:]) + "\n",
        encoding="utf-8",
    )
    logger.info(
        "[sorter] Historie oříznuta na posledních "
        f"{SORTER_HISTORY_MAX_ITEMS} záznamů (odstraněno {overflow})."
    )


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
        # Fallback na HTML část — odstraní tagy pro čitelný text
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                payload = part.get_payload(decode=True)
                if payload:
                    html = payload.decode("utf-8", errors="replace")
                    return re.sub(r"<[^>]+>", " ", html).strip()
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

    max_seen_uid = 0

    for uid, data in messages.items():
        max_seen_uid = max(max_seen_uid, int(uid))
        try:
            raw = data[b"BODY[]"]
            msg = email_lib.message_from_bytes(raw)

            subject = _decode_header(msg.get("Subject", "(bez předmětu)"))
            sender = _decode_header(msg.get("From", ""))
            message_id, email_key = _message_key(msg, raw)
            folder = "INBOX"
            uid_str = str(uid)
            list_id = _decode_header(msg.get("List-ID", ""))
            if email_key in logged_sort_keys:
                stats["skipped"] += 1
                continue

            # Emaily od sebe sama vždy ponechat (vlastní newslettery apod.)
            if IMAP_USER and IMAP_USER.lower() in sender.lower():
                logger.info(f"[sorter] KEEP/self     | {sender} | {subject}")
                _log_sort(
                    sender,
                    subject,
                    "",
                    "KEEP",
                    "self",
                    message_id,
                    email_key,
                    uid=uid_str,
                    folder=folder,
                    list_id=list_id,
                )
                stats["kept"] += 1
                continue

            body = _extract_body(msg)
            rule = match_move_rule(sender, subject, body)
            if rule:
                logger.info(f"[sorter] MOVE/rule     | {sender} | {subject}")
                conn.move([uid], TARGET_FOLDER)
                _log_sort(
                    sender,
                    subject,
                    body,
                    "MOVE",
                    "rule",
                    message_id,
                    email_key,
                    uid=uid_str,
                    folder=folder,
                    list_id=list_id,
                    rule_type=rule["rule_type"],
                    rule_value=rule["rule_value"],
                )
                stats["moved"] += 1
                continue

            if _is_newsletter(msg):
                logger.info(f"[sorter] MOVE/hlavičky | {sender} | {subject}")
                conn.move([uid], TARGET_FOLDER)
                _log_sort(
                    sender,
                    subject,
                    "",
                    "MOVE",
                    "headers",
                    message_id,
                    email_key,
                    uid=uid_str,
                    folder=folder,
                    list_id=list_id,
                )
                stats["moved"] += 1
                continue

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
            _log_sort(
                sender,
                subject,
                body,
                decision,
                "ai",
                message_id,
                email_key,
                uid=uid_str,
                folder=folder,
                list_id=list_id,
            )
        except Exception as e:
            stats["errors"] += 1
            logger.error(f"[sorter] Chyba při zpracování UID {uid} ({label}): {e}", exc_info=True)

    if max_seen_uid:
        _set_last_seen_uid(max_seen_uid)

    return stats


def _find_history_record(email_key: str) -> Optional[dict]:
    if not email_key or not HISTORY_FILE.exists():
        return None

    with open(HISTORY_FILE, encoding="utf-8") as f:
        lines = f.read().splitlines()

    for line in reversed(lines):
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if record.get("email_key") == email_key:
            return record
    return None


def _find_uid_in_target_folder(conn: IMAPClient, message_id: str, fallback_uid: str) -> Optional[int]:
    conn.select_folder(TARGET_FOLDER)

    if message_id:
        matches = conn.search(["HEADER", "Message-ID", message_id])
        if matches:
            return int(matches[-1])

    if fallback_uid:
        try:
            uid_int = int(fallback_uid)
        except (TypeError, ValueError):
            return None

        if uid_int in conn.search(["ALL"]):
            return uid_int

    return None


def move_kept_email_to_spam(email_key: str, rule_mode: str = "content") -> dict:
    """
    Ruční korekce z dashboardu:
    1. přesune konkrétní email do spam složky
    2. uloží pravidlo MOVE pro další podobné emaily
    """
    with _process_lock:
        record = _find_history_record(email_key)
        if not record:
            raise ValueError("Email v historii sorteru nebyl nalezen.")
        if record.get("outcome") != "kept":
            raise ValueError("Přesun do spamu je povolen jen pro dříve ponechané emaily.")

        stored_uid = record.get("uid")
        message_id = record.get("message_id", "")
        folder = record.get("folder") or "INBOX"

        sender = record.get("from", "")
        subject = record.get("subject", "")
        body = record.get("body", "")
        list_id = record.get("list_id", "")
        rule = add_move_rule_from_email(
            sender,
            subject,
            body,
            rule_mode=rule_mode,
            source="dashboard",
        )

        conn = _connect()
        try:
            conn.select_folder(folder)
            # Najdi aktuální UID emailu v dané složce — uložené UID může být zastaralé
            # po předchozím přesunu (IMAP přiřazuje nové UID při každém přesunu mezi složkami).
            actual_uid = None
            if message_id:
                matches = conn.search(["HEADER", "Message-ID", message_id])
                if matches:
                    actual_uid = int(matches[-1])
            if actual_uid is None and stored_uid:
                try:
                    candidate = int(stored_uid)
                    if candidate in conn.search(["ALL"]):
                        actual_uid = candidate
                except (TypeError, ValueError):
                    pass
            if actual_uid is None:
                raise ValueError("Email nebyl nalezen v složce, nelze ho přesunout do spamu.")
            conn.move([actual_uid], TARGET_FOLDER)
        finally:
            conn.logout()

        _log_sort(
            sender,
            subject,
            body,
            "MOVE",
            "dashboard",
            message_id,
            email_key,
            uid=str(actual_uid),
            folder=folder,
            list_id=list_id,
            rule_type=rule["rule_type"],
            rule_value=rule["rule_value"],
            force=True,
        )

        logger.info(
            f"[sorter] Dashboard přesunul email {email_key} do '{TARGET_FOLDER}' "
            f"a uložil pravidlo {rule['rule_type']}={rule['rule_value']}"
        )
        return {
            "email_key": email_key,
            "spam_folder": TARGET_FOLDER,
            "rule_type": rule["rule_type"],
            "rule_value": rule["rule_value"],
            "rule_created": rule["created"],
        }


def _update_history_record_to_kept(email_key: str, new_uid: str) -> None:
    """Přepíše poslední 'moved' záznam daného email_key na 'kept' přímo v souboru."""
    if not HISTORY_FILE.exists():
        return
    lines = HISTORY_FILE.read_text(encoding="utf-8").splitlines()
    updated = False
    for i in range(len(lines) - 1, -1, -1):
        try:
            record = json.loads(lines[i])
        except json.JSONDecodeError:
            continue
        if record.get("email_key") == email_key and record.get("outcome") == "moved":
            record["outcome"] = "kept"
            record["decision"] = "KEEP"
            record["folder"] = "INBOX"
            record["uid"] = new_uid
            record["rule_type"] = ""
            record["rule_value"] = ""
            lines[i] = json.dumps(record, ensure_ascii=False)
            updated = True
            break
    if updated:
        HISTORY_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def remove_rule_and_restore_email(email_key: str, rule_type: str, rule_value: str) -> dict:
    """
    Zruší MOVE pravidlo a pokusí se vrátit konkrétní email ze spam složky zpět do INBOX.
    """
    with _process_lock:
        # Hledáme poslední záznam s outcome=="moved" — ne jen poslední záznam celkově,
        # protože po úspěšném restore se zapíše nový "kept" záznam se stejným email_key.
        record = None
        if HISTORY_FILE.exists():
            with open(HISTORY_FILE, encoding="utf-8") as f:
                lines = f.read().splitlines()
            for line in reversed(lines):
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if r.get("email_key") == email_key and r.get("outcome") == "moved":
                    record = r
                    break
        if not record:
            raise ValueError("Záznam o přesunutém emailu nebyl nalezen v historii.")

        message_id = record.get("message_id", "")
        fallback_uid = record.get("uid", "")
        sender = record.get("from", "")
        subject = record.get("subject", "")
        body = record.get("body", "")
        list_id = record.get("list_id", "")

        conn = _connect()
        try:
            target_uid = _find_uid_in_target_folder(conn, message_id, fallback_uid)
            email_found = target_uid is not None
            if email_found:
                conn.move([target_uid], "INBOX")
        finally:
            conn.logout()

        deleted = delete_move_rule(rule_type, rule_value)

        if not email_found and not deleted:
            raise ValueError("Email ve spam složce nebyl nalezen a pravidlo také neexistuje — možná již bylo dříve zrušeno.")
        if not email_found:
            raise ValueError("Pravidlo bylo zrušeno, ale email ve spam složce už nebyl nalezen (mohl být smazán nebo přesunut).")

        # Přepíšeme záznam v souboru: změníme outcome na "kept" a aktualizujeme uid/folder.
        # Přidání nového řádku by spoléhalo na deduplikaci v API; přímý přepis je spolehlivější.
        _update_history_record_to_kept(email_key, str(target_uid))

        logger.info(
            f"[sorter] Dashboard zrušil pravidlo {rule_type}={rule_value} "
            f"a vrátil email {email_key} do 'INBOX'"
        )
        return {
            "email_key": email_key,
            "rule_type": rule_type,
            "rule_value": rule_value,
            "restored_to": "INBOX",
        }


def _process_unseen(conn: IMAPClient) -> dict:
    """Zpracuje všechny nepřečtené emaily v inboxu."""
    with _process_lock:
        conn.select_folder("INBOX")
        uids = conn.search(["UNSEEN"])
        if not uids:
            return _empty_stats()

        last_seen_uid = _get_last_seen_uid()
        if last_seen_uid > 0:
            uids = [uid for uid in uids if int(uid) > last_seen_uid]
            if not uids:
                return _empty_stats()

        stats = _process_uids(conn, uids, "unseen")
        new = stats["kept"] + stats["moved"]
        if new > 0:
            logger.info(f"[sorter] Zpracováno {new} nových emailů (přeskočeno: {stats['skipped']})")
        return stats


def _prime_startup_cursor(conn: IMAPClient) -> int:
    highest_uid = _get_highest_inbox_uid(conn)
    _set_last_seen_uid(highest_uid)
    logger.info(f"[sorter] Startup baseline nastaven na UID {highest_uid}. Staré UNSEEN nepřebírám automaticky.")
    return highest_uid


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

            global _startup_cursor_primed
            if not _startup_cursor_primed:
                # Po novém startu procesu jen nastavíme baseline, aby redeploy/restart
                # nespustil dotřídění starého inboxu. Nové maily po startu už pojedou normálně.
                _prime_startup_cursor(conn)
                _startup_cursor_primed = True
            else:
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
