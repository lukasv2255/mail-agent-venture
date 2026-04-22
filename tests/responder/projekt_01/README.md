# Projekt 01 — Responder / E-shop s doplňky stravy

**Odesílatel:** `newagent7878@gmail.com` (Gmail API)
**Příjemce / inbox agenta:** `johnybb11@seznam.cz` (IMAP seznam.cz)

## Testovací emaily a očekávaný výsledek

| ID  | Předmět                         | Klasifikace | Očekávaný výsledek                              |
| --- | ------------------------------- | ----------- | ----------------------------------------------- |
| T01 | Dotaz na objednávku 4471        | A1          | Odpověď: odesláno, tracking CZ847392011         |
| T02 | Kde je moje zásilka - obj. 2280 | A1          | Odpověď: v přípravě, expedice do 2 dnů          |
| T03 | Dotaz na protein                | B1          | Odpověď z KB: 24g bílkovin, živočišný původ     |
| T04 | Protein a diabetes              | B2          | Opatrná odpověď: doporučit konzultaci s lékařem |
| T05 | Chci vrátit zboží               | A2          | Instrukce k vrácení: zabalit, formulář, adresa  |
| T06 | Poškozený produkt - reklamace   | ESC         | Telegram eskalace, agent neodpovídá             |
| T07 | Objednávka 9999                 | A1          | Odpověď: objednávka nenalezena, ověř číslo      |
| T08 | Spolupráce — nabídka reklamy    | UNK         | Bez odpovědi, pouze zalogovat                   |

## Skripty

| Soubor               | Účel                                                                                                   |
| -------------------- | ------------------------------------------------------------------------------------------------------ |
| `send_test_batch.py` | Odešle 8 testovacích emailů najednou — rychlý ruční test                                               |
| `run_week.py`        | Týdenní stability test — posílá ~100 emailů v průběhu 7 dní, monitoruje uptime agenta, generuje report |

### run_week.py

Spustíš jednou na začátku týdne, skript běží na pozadí celý týden sám.

```bash
# Spuštění — 7 dní, ~100 emailů
python3 tests/responder/projekt_01/run_week.py

# Rychlý test — 20 emailů za 30 minut
python3 tests/responder/projekt_01/run_week.py --fast

# Report z existujících logů
python3 tests/responder/projekt_01/run_week.py --report
```

**Co dělá:**

- Posílá emaily z 21 šablon (ORDER, PRODUCT, RETURN, ESC, SPAM, UNK) s realistickými váhami
- Každou minutu pinguje dashboard `/api/status` — detekuje pád agenta
- Loguje do `logs/responder/week_sent.jsonl` a `logs/responder/uptime.jsonl`
- Na konci (nebo Ctrl+C) vypíše report: uptime %, počet padů, sent vs. zpracováno
