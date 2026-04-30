# Newsletter snapshots

Skript v tomhle adresáři slouží jako ruční denní běh newsletteru bez odesílání:

- vygeneruje nový newsletter (scrape + LLM)
- uloží ho jako snapshot do `tests/newsletter/projekt01/snapshots/YYYY-MM-DD.txt`
- spočítá podobnost vs. předchozí snapshoty a zapíše report do `tests/newsletter/projekt01/snapshots/report.jsonl`

Spuštění:

```bash
python3 tests/newsletter/run_daily_snapshot.py
```

Jen scoring (bez generování nového snapshotu):

```bash
python3 tests/newsletter/run_daily_snapshot.py --no-generate
```

Poznámka: Skript volá interní funkce newsletter modulu a vyžaduje `OPENAI_API_KEY`.
Používá testovací prompty z `tests/newsletter/projekt01/` (nastaví `PROMPTS_DIR`) a ukládá stav do `tests/newsletter/projekt01/data/` (nastaví `DATA_DIR`).
