#!/usr/bin/env python3
"""
Denní snapshot newsletteru (bez odesílání).

Cíl:
- Každý den vygenerovat newsletter (scrape + LLM) a uložit ho do tests artefaktů
- Spočítat podobnost (Jaccard nad shingles) vůči předchozím snapshotům

Použití:
  python3 tests/newsletter/run_daily_snapshot.py

Požadavky:
- síť (DDG scraping)
- OPENAI_API_KEY (pro generování obsahu)
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _snapshots_dir() -> Path:
    return _repo_root() / "tests" / "newsletter" / "projekt01" / "snapshots"


def _report_file() -> Path:
    return _snapshots_dir() / "report.jsonl"


def _today_slug() -> str:
    return date.today().isoformat()

def _list_snapshots() -> list[Path]:
    d = _snapshots_dir()
    if not d.exists():
        return []
    return sorted(p for p in d.glob("*.txt") if p.is_file())


def _load_text(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _write_text(p: Path, text: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def _append_jsonl(p: Path, obj: dict) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--no-generate",
        action="store_true",
        help="Jen přepočítá scoring ze stávajících snapshotů (bez generování nového).",
    )
    parser.add_argument(
        "--k",
        type=int,
        default=7,
        help="Velikost shingle pro podobnost (default: 7).",
    )
    args = parser.parse_args()

    # Izolace pro testovací instanci: používej projektové prompty v tests/
    # a ukládej data (last_sent, domain stats) do tests/ artefaktů.
    project_root = _repo_root() / "tests" / "newsletter" / "projekt01"
    os.environ.setdefault("PROMPTS_DIR", str(project_root))
    os.environ.setdefault("DATA_DIR", str(project_root / "data"))

    # Umožni import `src.*` při spuštění jako skript z rootu repo.
    sys.path.insert(0, str(_repo_root()))

    # Zkus načíst lokální .env (pokud existuje). launchd nemá shell env.
    try:
        from dotenv import load_dotenv  # type: ignore

        load_dotenv(_repo_root() / ".env")
    except Exception:
        pass

    # Import uvnitř (až po argparse), aby byl start rychlý a šel použít i jen scoring.
    from src.modules import newsletter as nl  # noqa: WPS433

    # Pokud OPENAI_API_KEY není v lokálním env, zkus ho načíst z Railway (linked project).
    if not os.getenv("OPENAI_API_KEY"):
        try:
            res = subprocess.run(
                ["railway", "variable", "list", "--json"],
                cwd=str(_repo_root()),
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(res.stdout or "{}")
            # Railway CLI vrací různé tvary; bereme jak list, tak mapu.
            key = None
            if isinstance(payload, list):
                for item in payload:
                    if (item or {}).get("name") == "OPENAI_API_KEY":
                        key = (item or {}).get("value")
                        break
            elif isinstance(payload, dict):
                # varianta: { "OPENAI_API_KEY": "..." }
                key = payload.get("OPENAI_API_KEY")
                if key is None and "variables" in payload and isinstance(payload["variables"], list):
                    for item in payload["variables"]:
                        if (item or {}).get("name") == "OPENAI_API_KEY":
                            key = (item or {}).get("value")
                            break
            if key:
                os.environ["OPENAI_API_KEY"] = str(key)
        except Exception:
            # Best-effort. Pokud to nepůjde, spadne to při _generate_content s jasnou chybou.
            pass

    snapshots = _list_snapshots()

    if not args.no_generate:
        day = date.today()
        slug = day.isoformat()
        out_file = _snapshots_dir() / f"{slug}.txt"
        if out_file.exists() and out_file.stat().st_size > 0:
            print(f"Snapshot pro {slug} už existuje: {out_file}")
        else:
            print("Sbírám data z webu…")
            raw = nl._collect_data()
            print("Generuji newsletter…")
            content = nl._generate_content(raw, today=day)
            _write_text(out_file, content)
            print(f"Uloženo: {out_file}")
        snapshots = _list_snapshots()

    if len(snapshots) < 2:
        print("Není dost snapshotů pro scoring (potřeba alespoň 2).")
        return 0

    # Skóruj vždy poslední snapshot vůči předchozím (prev + 7-day okno).
    latest = snapshots[-1]
    latest_text = _load_text(latest)
    latest_sh = nl._shingles(latest_text, k=args.k)

    def score(a: Path, b: Path) -> dict:
        a_text = _load_text(a)
        a_sh = nl._shingles(a_text, k=args.k)
        sim = nl._jaccard(a_sh, latest_sh)
        return {
            "a": a.name,
            "b": b.name,
            "similarity": sim,
            "change": 1.0 - sim,
        }

    prev = snapshots[-2]
    prev_score = score(prev, latest)

    window = snapshots[-8:-1]  # max 7 předchozích + latest
    window_scores = [score(p, latest) for p in window]
    best_match = max(window_scores, key=lambda x: x["similarity"])

    payload = {
        "date": latest.stem,
        "snapshot": latest.name,
        "k": args.k,
        "prev": prev_score,
        "best_match_last_7": best_match,
    }
    _append_jsonl(_report_file(), payload)

    print("\nScoring:")
    print(f"- latest: {latest.name}")
    print(f"- prev:   {prev.name}  sim={prev_score['similarity']:.3f}  change={prev_score['change']:.3f}")
    print(
        f"- best7:  {best_match['a']}  sim={best_match['similarity']:.3f}  change={best_match['change']:.3f}"
    )
    print(f"- report: {_report_file()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
