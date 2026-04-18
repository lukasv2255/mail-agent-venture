# Mail Agent

## Infrastruktura

- **Railway token:** `e2b4b43c-b5c1-4ab8-9885-70d936782acc`
- **Railway Project ID:** `2e231bd5-5020-4327-8df5-e059f0fcbb8a`
- **Railway Service ID:** `814fa52b-18b6-4e3c-8127-85cbae48eb16`
- **GitHub:** `https://github.com/lukasv2255/mail-agent`
- **Gmail:** `newagent7878@gmail.com`
- **Telegram Chat ID:** `479991910`

## Project Memory

Před každou prací zkontroluj:

- `docs/project_notes/key_facts.md` — API klíče, porty, endpointy, konfigurace
- `docs/project_notes/decisions.md` — co a proč jsme zvolili
- `docs/project_notes/bugs.md` — problémy které jsme už řešili
- `tasks/lessons.md` — co se neosvědčilo, co opakovat

Po každé opravě nebo poučení aktualizuj příslušný soubor.

## Task Management

- Netriviální úkol (3+ kroky) → nejdřív plan do `tasks/todo.md`
- Po každé korekci → přidej poučení do `tasks/lessons.md`
- Na začátku session → přečti `tasks/lessons.md`

## Spouštění

- **Lokální testování:** `python3 main.py` — jediný způsob, přímo v terminálu
- **Produkce (Railway):** Railway spouští `python3 main.py` automaticky
- `tray.py` byl odstraněn — nepoužívat, způsoboval více instancí najednou

## Newsletter modul (MODULE_NEWSLETTER)

Env proměnné pro aktivaci:

```
MODULE_NEWSLETTER=true
NEWSLETTER_DAY=0           # den odeslání: 0=pondělí, 1=úterý ... 6=neděle (default 0)
NEWSLETTER_HOUR=7          # hodina odeslání (default 7)
NEWSLETTER_MINUTE=0        # minuta odeslání (default 0)

# Gmail (MAIL_CLIENT=gmail):
GMAIL_ADDRESS=xxx@gmail.com   # odesílatel i příjemce (posílá sám sobě)

# IMAP/SMTP (MAIL_CLIENT=imap):
IMAP_USER=xxx@domena.cz
IMAP_PASSWORD=xxx
SMTP_HOST=smtp.domena.cz
SMTP_PORT=587
```

Příkaz `/newsletter` v Telegamu odešle newsletter okamžitě (bez čekání na pondělí).

## QA

Před prací na dashboardu přečti `docs/qa/dashboard.md`.
