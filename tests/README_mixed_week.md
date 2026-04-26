# Mixed Week Test

Jeden centrální skript v rootu `tests/`, který během týdne odešle mix 1000 emailů
na testovací inbox a pokryje všechny emailové scénáře, které v repo už používáme.

**Skript:** `tests/run_mixed_week.py`
**Výchozí příjemce:** `johnybb11@seznam.cz`
**Očekávaný odesílatel Gmail API:** `newagent7878@gmail.com`

## Co zahrnuje

Skript bere scénáře přímo z existujících testů:

- `tests/sorter/test_sorter.py`
- `tests/responder/run_week.py`
- `tests/email_body/send_html_body_test.py`

Tím pádem jsou v mixu:

- sorter spamy
- sorter poptávky / relevantní B2B maily
- sorter newslettery
- responder order / product / return / escalation / spam / unknown
- email body scénáře: plain text, multipart, HTML-only, Apple Mail HTML
- persist scénář: identické maily pro ruční ověření pravidla a následného matchnutí

## Co naopak nezahrnuje

Tyto testy nejsou o reálném odesílání emailů do inboxu, takže do mixu nepatří:

- `tests/data_persistence/`
- `tests/sorter_state/`
- `tests/newsletter/`

## Formát subjectu

Každý email dostane prefix:

```text
[MIX-scenario-type-templateid-0001] Původní subject
```

Příklad:

```text
[MIX-sorter-SPAM-S03-0001] Vydělávejte z domova 50 000 Kč měsíčně — bez zkušeností!
```

To znamená:

- `scenario`: odkud scénář pochází (`sorter`, `responder`, `email-body`)
- `type`: typ uvnitř scénáře (`SPAM`, `ORDER`, `HTML_ONLY`, ...)
- `templateid`: konkrétní test case
- poslední číslo: pořadí emailu v běhu

U `persist` scénáře jsou v poolu záměrně dva identické maily se stejným subjectem i body.
Liší se jen `templateid` v prefixu, aby šly dohledat jako dvě samostatná odeslání.

## Jak to funguje

- Výchozí běh pošle `1000` emailů během `7` dní.
- Všechny známé scénáře se pošlou aspoň jednou.
- Zbytek se domixuje náhodně s váhami:
  - `sorter`: 50 %
  - `responder`: 35 %
  - `email-body`: 15 %
- Odeslání se rozprostře rovnoměrně přes celý interval s menším jitterem, aby to nepůsobilo strojově.

## Spuštění

```bash
python3 tests/run_mixed_week.py
```

Rychlá validace:

```bash
python3 tests/run_mixed_week.py --fast
```

`--fast` pošle `30` mixovaných emailů okamžitě, bez rozložení v čase.
Je to smoke test, takže negarantuje pokrytí úplně všech unikátních scénářů.
Garantuje ale přítomnost `persist` dvojice identických mailů.

Jen report z existujících logů:

```bash
python3 tests/run_mixed_week.py --report
```

## Volby

```bash
python3 tests/run_mixed_week.py --count 1000 --days 7
python3 tests/run_mixed_week.py --target johnybb11@seznam.cz
python3 tests/run_mixed_week.py --seed 42
```

Pokud je Gmail API přihlášené jiným účtem než `newagent7878@gmail.com`, skript běh
zastaví. Vědomé obejití:

```bash
python3 tests/run_mixed_week.py --allow-other-sender
```

## Logy

Skript zapisuje do:

- `logs/mixed_week/week_sent.jsonl`
- `logs/mixed_week/week_report.txt`

`week_sent.jsonl` obsahuje každý pokus o odeslání včetně:

- pořadí emailu
- scénáře
- typu
- template ID
- výsledného subjectu

## Doporučené použití

1. Přihlas Gmail API jako `newagent7878@gmail.com`.
2. Spusť `python3 tests/run_mixed_week.py`.
3. Nech skript běžet celý týden.
4. Průběžně kontroluj inbox `johnybb11@seznam.cz`, dashboard a logy.
5. Na konci si vytáhni souhrn přes `--report`.
