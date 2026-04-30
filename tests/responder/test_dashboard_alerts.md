# Dashboard Alerts — ESC a UNK připnuté emaily

**Typ testů:** unit / API (pytest, bez odesílání emailů)
**Modul:** `src/dashboard.py`, `src/notifier.py`
**Endpointy:** `GET /api/status` (pole `alerts`), `POST /api/alert/dismiss/{index}`

## Co testují

| ID   | Co se testuje                                                       | Endpoint                   |
| ---- | ------------------------------------------------------------------- | -------------------------- |
| DA01 | Prázdný seznam alertů → `alerts == []`                              | GET /api/status            |
| DA02 | ESC email je v alertech se správným typem, odesílatelem a předmětem | GET /api/status            |
| DA03 | UNK email je v alertech se správným typem                           | GET /api/status            |
| DA04 | Obě varianty najednou — ESC i UNK jsou viditelné                    | GET /api/status            |
| DA05 | Tělo emailu je zkráceno na max 300 znaků                            | GET /api/status            |
| DA06 | Odepnutí ESC alertu ho odstraní ze seznamu                          | POST /api/alert/dismiss/0  |
| DA07 | Odepnutí UNK alertu ho odstraní ze seznamu                          | POST /api/alert/dismiss/0  |
| DA08 | Odepnutí správného indexu při více alertech současně                | POST /api/alert/dismiss/0  |
| DA09 | Index mimo rozsah nepadí (nulový seznam alertů, index 99)           | POST /api/alert/dismiss/99 |
| DA10 | Dismiss zavolá `unpin_callback` s `message_id`                      | POST /api/alert/dismiss/0  |
| DA11 | Bez `message_id` se `unpin_callback` nevolá                         | POST /api/alert/dismiss/0  |

## Testovací data

Emaily jsou definované přímo v testu — neodesílají se přes Gmail API:

| Proměnná    | from                    | subject                       | email_type |
| ----------- | ----------------------- | ----------------------------- | ---------- |
| `ESC_EMAIL` | `jan.novak@example.com` | Poškozený produkt - reklamace | ESC        |
| `UNK_EMAIL` | `reklama@firma.cz`      | Spolupráce — nabídka reklamy  | UNK        |

## Spuštění

```bash
# standalone
python3 -m pytest tests/responder/test_dashboard_alerts.py -v

# jako součást týdenního runu — jen responder skupina
python3 tests/run_mixed_week.py --responder --fast

# jen dashboard unit testy (bez odesílání emailů)
python3 tests/run_mixed_week.py --dashboard
```

## Skripty

| Soubor                     | Účel                                                            |
| -------------------------- | --------------------------------------------------------------- |
| `test_dashboard_alerts.py` | 11 pytest testů pro dashboard API — zobrazení a odepnutí alertů |
| `test_responder.py`        | Odešle 8 testovacích emailů — ruční E2E test responderu         |

Pro týdenní stability test viz `tests/run_mixed_week.py` — pokrývá sorter, responder i email_body dohromady.
