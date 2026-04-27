"""
Perzistentní ruční pravidla pro sorter.

Pravidla ukládáme odděleně od historie, aby přežila restart i redeploy
v prostředí s persistentním DATA_DIR.
"""
import hashlib
import logging
import sqlite3
from datetime import datetime, timezone
from email.utils import parseaddr
from typing import Optional

from src.config import DATA_DIR

logger = logging.getLogger(__name__)

RULES_DB = DATA_DIR / "sorter_rules.db"


def _connect() -> sqlite3.Connection:
    RULES_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(RULES_DB)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sorter_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rule_type TEXT NOT NULL,
            rule_value TEXT NOT NULL,
            action TEXT NOT NULL,
            source TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(rule_type, rule_value, action)
        )
        """
    )
    return conn


def _normalize(value: str) -> str:
    return (value or "").strip().lower()


def _normalize_content(value: str) -> str:
    return " ".join((value or "").replace("\r", "\n").split()).strip().lower()


def build_content_rule_value(subject: str, body: str) -> str:
    normalized_subject = _normalize_content(subject)
    normalized_body = _normalize_content(body)[:1500]
    raw = "\n".join([normalized_subject, normalized_body]).strip()
    return hashlib.sha256(raw.encode("utf-8")).hexdigest() if raw else ""


def build_sender_rule_value(sender: str) -> str:
    _, address = parseaddr(sender or "")
    return _normalize(address or sender)


def add_move_rule(rule_type: str, rule_value: str, source: str = "dashboard") -> bool:
    normalized = _normalize(rule_value)
    if not normalized:
        raise ValueError("Prázdná hodnota pravidla.")

    created = datetime.now(timezone.utc).isoformat()
    with _connect() as conn:
        cursor = conn.execute(
            """
            INSERT OR IGNORE INTO sorter_rules (rule_type, rule_value, action, source, created_at)
            VALUES (?, ?, 'MOVE', ?, ?)
            """,
            (rule_type, normalized, source, created),
        )
        created_new = cursor.rowcount > 0

    if created_new:
        logger.info(f"[sorter-rules] Přidáno pravidlo MOVE: {rule_type}={normalized}")
    return created_new


def delete_move_rule(rule_type: str, rule_value: str) -> bool:
    normalized = _normalize(rule_value)
    if not rule_type:
        raise ValueError("Chybí typ pravidla.")
    if not normalized:
        raise ValueError("Prázdná hodnota pravidla.")

    with _connect() as conn:
        cursor = conn.execute(
            """
            DELETE FROM sorter_rules
            WHERE action = 'MOVE' AND rule_type = ? AND rule_value = ?
            """,
            (rule_type, normalized),
        )
        deleted = cursor.rowcount > 0

    if deleted:
        logger.info(f"[sorter-rules] Smazáno pravidlo MOVE: {rule_type}={normalized}")
    return deleted


def add_move_rule_from_email(
    sender: str,
    subject: str,
    body: str,
    *,
    rule_mode: str = "content",
    source: str = "dashboard",
) -> dict:
    if rule_mode == "sender":
        sender_value = build_sender_rule_value(sender)
        if not sender_value:
            raise ValueError("Email nemá použitelnou adresu odesílatele pro pravidlo.")
        created = add_move_rule("from_address", sender_value, source=source)
        return {
            "rule_type": "from_address",
            "rule_value": sender_value,
            "created": created,
        }

    if rule_mode == "content":
        content_hash = build_content_rule_value(subject, body)
        if not content_hash:
            raise ValueError("Email nemá použitelný obsah pro pravidlo.")
        created = add_move_rule("content_hash", content_hash, source=source)
        return {
            "rule_type": "content_hash",
            "rule_value": content_hash,
            "created": created,
        }

    raise ValueError(f"Neznámý rule_mode='{rule_mode}'.")


def add_keep_rule(sender: str, source: str = "dashboard") -> dict:
    sender_value = build_sender_rule_value(sender)
    if not sender_value:
        raise ValueError("Email nemá použitelnou adresu odesílatele pro KEEP pravidlo.")
    created_at = datetime.now(timezone.utc).isoformat()
    with _connect() as conn:
        cursor = conn.execute(
            """
            INSERT OR IGNORE INTO sorter_rules (rule_type, rule_value, action, source, created_at)
            VALUES (?, ?, 'KEEP', ?, ?)
            """,
            ("from_address", sender_value, source, created_at),
        )
        created = cursor.rowcount > 0
    if created:
        logger.info(f"[sorter-rules] Přidáno pravidlo KEEP: from_address={sender_value}")
    return {"rule_type": "from_address", "rule_value": sender_value, "created": created}


def match_keep_rule(sender: str) -> Optional[dict]:
    sender_value = build_sender_rule_value(sender)
    if not sender_value:
        return None
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT id, rule_type, rule_value, action, source, created_at
            FROM sorter_rules
            WHERE action = 'KEEP' AND rule_type = 'from_address' AND rule_value = ?
            LIMIT 1
            """,
            (sender_value,),
        ).fetchone()
    return dict(row) if row else None


def match_move_rule(sender: str, subject: str, body: str) -> Optional[dict]:
    candidates = []
    sender_value = build_sender_rule_value(sender)
    if sender_value:
        candidates.append(("from_address", sender_value))

    content_hash = build_content_rule_value(subject, body)
    if content_hash:
        candidates.append(("content_hash", content_hash))

    if not candidates:
        return None

    with _connect() as conn:
        for rule_type, rule_value in candidates:
            row = conn.execute(
                """
                SELECT id, rule_type, rule_value, action, source, created_at
                FROM sorter_rules
                WHERE action = 'MOVE' AND rule_type = ? AND rule_value = ?
                LIMIT 1
                """,
                (rule_type, rule_value),
            ).fetchone()
            if row:
                return dict(row)

    return None
