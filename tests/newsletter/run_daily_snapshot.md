# run_daily_snapshot — denní newsletter snapshoty (projekt01)

Tento testovací skript slouží k offline/integration ověření, jak se newsletter v čase “mění”, bez odesílání emailů.

## Co dělá

- Provede sběr dat z webu (DuckDuckGo + případně `site:` zdroje) stejně jako modul newsletter.
- Vygeneruje newsletter přes OpenAI (LLM) pro každý simulovaný den.
- Uloží výstup jako snapshot soubor `YYYY-MM-DD.txt`.
- Spočítá podobnost (Jaccard nad shingles) mezi snapshoty a zapíše report do JSONL.

## Kam ukládá artefakty

- Snapshots: `tests/newsletter/projekt01/snapshots/YYYY-MM-DD.txt`
- Report (JSONL, 1 řádek na běh): `tests/newsletter/projekt01/snapshots/report.jsonl`
- Stav pro newsletter modul (domain stats, last_sent, …): `tests/newsletter/projekt01/data/`

Skript automaticky nastaví:

- `PROMPTS_DIR=tests/newsletter/projekt01`
- `DATA_DIR=tests/newsletter/projekt01/data`

Tím pádem používá projektové prompty z `tests/newsletter/projekt01/` (např. `newsletter_format.md`, `newsletter_queries.txt`) a neznečišťuje produkční `data/`.

## Spuštění

Denní ruční běh (1 snapshot):

```bash
python3 tests/newsletter/run_daily_snapshot.py
```

Jen přepočet scoringu ze stávajících snapshotů (bez generování):

```bash
python3 tests/newsletter/run_daily_snapshot.py --no-generate
```

## Předpoklady

- `OPENAI_API_KEY` je dostupný v env (lokálně), nebo je projekt připojený k Railway a skript ho zkusí načíst přes `railway variable list --json`.
- Síť (kvůli web sběru).

## Výstup / očekávání

- Po prvním běhu existuje alespoň 1 snapshot soubor.
- Po 2+ snímcích se začne generovat `report.jsonl` s poli `similarity` a `change` (0–1).
