"""
KB loader — načte knowledge base podle KB_SOURCE env proměnné.

Dostupné hodnoty KB_SOURCE:
  file  — čte z prompts/ adresáře (výchozí, pro demo a dev)
  db    — čte z databáze klienta (pro produkci)

Použití:
  from src.kb_loader import load_kb
  kb = load_kb()   # vrátí string který jde přímo do systémového promptu
"""
import logging
import os

logger = logging.getLogger(__name__)

KB_SOURCE = os.getenv("KB_SOURCE", "file")

KB_DIR = os.path.join(os.path.dirname(__file__), "..", "prompts")


def load_kb() -> str:
    """Vrátí obsah KB jako string pro vložení do systémového promptu."""
    if KB_SOURCE == "file":
        return _load_from_files()
    elif KB_SOURCE == "db":
        return _load_from_db()
    else:
        raise ValueError(f"Neznámý KB_SOURCE='{KB_SOURCE}'. Možnosti: file, db")


def _load_from_files() -> str:
    """Načte všechny .md a .txt soubory z prompts/ (kromě classifier a response promptů)."""
    kb_parts = []

    for filename in sorted(os.listdir(KB_DIR)):
        if not (filename.endswith(".md") or filename.endswith(".txt")):
            continue
        # classifier_prompt a response_* jsou systémové prompty, ne KB
        if filename.startswith("classifier_prompt") or filename.startswith("response_"):
            continue

        filepath = os.path.join(KB_DIR, filename)
        with open(filepath, encoding="utf-8") as f:
            content = f.read().strip()
        if content:
            kb_parts.append(content)
            logger.debug(f"KB: načten soubor {filename}")

    if not kb_parts:
        logger.warning("KB je prázdná — v prompts/ nejsou žádné KB soubory.")
        return ""

    return "\n\n---\n\n".join(kb_parts)


def _load_from_db() -> str:
    """Načte KB z databáze klienta. Implementuj podle konkrétního projektu."""
    import psycopg2

    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor()

    # Příklad — upravit podle schématu klienta:
    # cur.execute("SELECT nazev, popis FROM produkty WHERE aktivni = true")
    # rows = cur.fetchall()
    # return "\n".join(f"{r[0]}: {r[1]}" for r in rows)

    conn.close()
    raise NotImplementedError("_load_from_db() není implementována pro tento projekt.")
