# Mail Agent

## Project Memory

Před prací zkontroluj relevantní projektovou paměť:

- `docs/key_facts.md` — konfigurace, porty, endpointy, důležité soubory
- `docs/decisions.md` — architektonická rozhodnutí
- `docs/bugs.md` — známé a vyřešené chyby
- `tasks/lessons.md` — poučení a pravidla z práce na projektu

Po opravě, poučení nebo změně pravidla aktualizuj příslušný soubor.

## Trigger Fráze

- **"nauč se"** = ulož dané pravidlo nebo poznatek do projektového nebo lokálního `.md` souboru podle kontextu.
- **"dokumentuj"** = zapiš informaci do aktuální projektové paměti, typicky `tasks/lessons.md`, `docs/bugs.md`, nebo jiného relevantního memory dokumentu.
- **"run"** = spusť agenta: primárně Railway (zkontroluj logy tam), pokud Railway neběží, fallback na launchd (localhost).

Tyto fráze ber jako explicitní pokyn k perzistentnímu zápisu nebo akci, ne jako běžnou konverzační formulaci.

## Spouštění

- **Primární:** agent běží na Railway. Stav a logy kontroluj tam.
- **Fallback:** pokud Railway neběží, agent běží lokálně přes launchd (dashboard na localhost).
- Nikdy nespouštěj agenta ručně přes `python3 main.py` — vždy přes Railway nebo launchd.
- Launchd: instalace/regenerace plistu: `python3 scripts/install_launchd.py`, start/stop přes `launchctl`.
- Testovací skripty v `tests/` se mohou spouštět ručně.

## Template Zásady

- Projekt je template pro klientské instance.
- Žádné absolutní cesty v kódu.
- Klientské hodnoty patří do `.env`, ne do kódu ani do `CLAUDE.md`.
- `.env`, tokeny, credentials a logy necommitovat.
- Do gitu patří `.env.example` a template soubory.
- launchd plist v repu je šablona: `launchd/com.mailagent.plist.template`.
- Konkrétní launchd plist generuje `scripts/install_launchd.py` podle aktuální složky.

## Logování

- Provozní logy hlavního agenta:
  - `logs/agent.log`
  - `logs/agent_err.log`
  - `logs/uptime.jsonl`
- Modulové historie:
  - `logs/responder/responses.jsonl`
  - `logs/sorter/sorter.jsonl`
- Testovací logy patří do příslušných podsložek v `logs/responder/` nebo `logs/sorter/`.

## Bezpečnost

- Nikdy neukládej tokeny, hesla, Chat ID, credentials ani klientské identifikátory do `CLAUDE.md`.
- Pokud se tajný údaj objeví v commitu nebo sdíleném souboru, ber ho jako kompromitovaný a doporuč rotaci.
- Neprováděj destruktivní git nebo mailbox operace bez výslovného pokynu.

## Modulové Poznámky

- `sorter` třídí inbox a nemá měnit stav `seen/unseen`, pokud to uživatel výslovně nechce.
- `/sort` je ruční třídění existujícího INBOXu přes Telegram.
- `responder` řeší odpovědi a schvalování.
- `newsletter` generuje a odesílá newsletter; `/newsletter` ho spustí okamžitě.

## QA

- Před prací na dashboardu přečti `docs/qa/dashboard.md`.
- Po změnách v Pythonu spusť minimálně `py_compile` pro dotčené soubory.
- U běžícího agenta ověř stav přes Railway logy (primárně) nebo launchd (fallback), ne spuštěním druhé instance.
