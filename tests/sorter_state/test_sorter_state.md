# Test: UID watermark — správné chování sorteru po restartu

**Datum:** 2026-04-25
**Cíl:** Ověřit, že sorter po restartu nezpracuje znovu staré emaily a zachytí pouze nové.

Automatické unit testy jsou v `tests/sorter/test_sorter_state.py`.
Tento dokument popisuje manuální integrační ověření na živém agentovi.

---

## Co testujeme

Sorter sleduje nejvyšší zpracované UID v `data/sorter/state.json` (watermark).
Při startu nastaví cursor na maximum existujících UID — takže staré emaily přeskočí.
Po restartu zpracuje jen emaily s UID vyšším než uložený watermark.

---

## Krok 1: Ověř, že state.json existuje a má správný obsah

```bash
cat data/sorter/state.json
```

Očekávaný výstup (příklad):

```json
{ "last_seen_uid": 1042 }
```

Pokud soubor neexistuje — agent ještě neběžel nebo `DATA_DIR` míří jinam.

---

## Krok 2: Zjisti aktuální watermark a UID v inboxu

Přes Railway CLI nebo lokálně:

```bash
python3 -c "
from src.config import DATA_DIR
from src.modules.sorter import _get_last_seen_uid
print('Watermark:', _get_last_seen_uid())
print('State file:', DATA_DIR / 'sorter' / 'state.json')
"
```

Zapiš si hodnotu watermarku — po restartu musí být stejná nebo vyšší.

---

## Krok 3: Pošli testovací email a proveď check

Pošli email (viz `feedback_test_emails_routing.md`):

```
FROM: <libovolný odesílatel>
TO:   johnybb11@seznam.cz
```

Spusť `/check` v Telegramu nebo `POST /api/check`.

Ověř v `logs/sorter/sorter.jsonl`, že email byl zpracován (outcome `moved` nebo `kept`).
Watermark se musí zvýšit — znovu ověř:

```bash
python3 -c "from src.modules.sorter import _get_last_seen_uid; print(_get_last_seen_uid())"
```

---

## Krok 4: Restartuj agenta

```bash
launchctl stop com.mailagent
launchctl start com.mailagent
```

Počkej ~5 sekund na inicializaci.

---

## Krok 5: Ověř, že email nebyl zpracován znovu

Po restartu spusť znovu `/check`.

V `logs/sorter/sorter.jsonl` **nesmí** přibýt nový záznam pro stejný email.

**Úspěch:** Email se neobjeví znovu — watermark funguje správně.
**Selhání:** Email je zpracován dvakrát — `state.json` se nezapsal, nebo `DATA_DIR` není perzistentní.

---

## Krok 6: Ověř, že nový email po restartu projde normálně

Pošli druhý testovací email (po restartu) a spusť `/check`.

**Úspěch:** Nový email je zpracován, watermark se aktualizuje.
**Selhání:** Nový email je přeskočen — cursor se nastavil příliš vysoko (bug v `_prime_startup_cursor`).

---

## Unit testy (automatické)

`tests/sorter/test_sorter_state.py` pokrývá tři scénáře bez potřeby Gmail nebo sítě:

| Test                                                                           | Co ověřuje                                                   |
| ------------------------------------------------------------------------------ | ------------------------------------------------------------ |
| `test_prime_startup_cursor_sets_highest_current_uid`                           | Cursor se při startu nastaví na max UID v inboxu             |
| `test_prime_startup_cursor_overwrites_older_cursor_without_processing_backlog` | Starý cursor se přepíše novým maximem, backlog se nezpracuje |
| `test_process_unseen_only_passes_newer_uids_than_watermark`                    | Agent zpracuje jen UID vyšší než watermark                   |

Spuštění:

```bash
python3 tests/sorter/test_sorter_state.py
```

---

## Možné příčiny selhání

| Problém                        | Příčina                                                          | Oprava                                       |
| ------------------------------ | ---------------------------------------------------------------- | -------------------------------------------- |
| `state.json` chybí po restartu | `DATA_DIR` není perzistentní (Railway bez Volume)                | Viz `tests/test_data_persistence_railway.md` |
| Email zpracován dvakrát        | Zápis watermarku selhal (výjimka před `_set_last_seen_uid`)      | Zkontroluj logy agenta                       |
| Nový email přeskočen           | `_prime_startup_cursor` přepsal cursor na příliš vysokou hodnotu | Zkontroluj pořadí volání v `sorter.py`       |
