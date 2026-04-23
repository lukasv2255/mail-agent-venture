# Template Setup

Projekt se má chovat jako šablona pro další klientské instance. Kód nesmí
obsahovat absolutní cesty na konkrétní checkout, například
`/Users/.../mail-agent`. Instance se liší konfigurací v `.env`, prompty a
deploymentem.

## Princip

Kód odvozuje cesty podle vlastního umístění:

```python
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
```

Centrální konfigurace je v `src/config.py`:

```python
PROJECT_ROOT
LOG_DIR
DATA_DIR
PROMPTS_DIR
TEMPLATES_DIR
```

Každou cestu lze přepsat přes env proměnnou. Relativní hodnota se bere relativně
k `PROJECT_ROOT`, absolutní hodnota se použije beze změny.

## Pravidla

- Žádné absolutní cesty v Python kódu.
- Runtime data patří pod `LOG_DIR` nebo `DATA_DIR`.
- Prompty patří pod `PROMPTS_DIR`.
- Klientské hodnoty patří do `.env`.
- Do gitu patří `.env.example`, ne `.env`.
- launchd soubor v gitu je pouze template.

## Finální klientský wizard

Pro finální spuštění s klientem u počítače použij:

```bash
python3 scripts/client_instance_wizard.py
```

Tenhle wizard je určený pro okamžik, kdy už se rozhoduje konkrétní klientská
instance. Ptá se postupně, validuje číselné hodnoty a nedovolí inline komentáře
v env hodnotách typu:

```env
NEWSLETTER_INTERVAL_DAYS=1 # spatne
```

Správně zapisuje jen čistou hodnotu:

```env
NEWSLETTER_INTERVAL_DAYS=1
```

### Co wizard vytvoří

- `.env` — lokální/runtime konfigurace instance
- `.env.railway` — stejná sada proměnných připravená pro Railway dashboard/CLI
- `NEXT_STEPS.md` — checklist bez tajných hodnot

Soubory `.env` a `.env.railway` jsou ignorované gitem. Nepatří do commitu.

### Režimy startu

Wizard se zeptá na startovací režim:

- `demo` — bezpečný testovací režim, `DRY_RUN=true`, responder vypnutý
- `pilot` — reálný mailbox, sorter zapnutý, responder vypnutý
- `production` — produkční režim, responder/newsletter podle rozhodnutí

Doporučený první den u klienta je `pilot`:

```env
MODULE_SORTER=true
MODULE_RESPONDER=false
MODULE_NEWSLETTER=false
DRY_RUN=false
AUTO_RESPOND=false
```

Responder a newsletter zapínej až po kontrole dashboardu a logů.

### Na co se ptá

1. název klienta/projektu
2. kde instance poběží: `railway`, `launchd`, nebo `both`
3. startovací režim: `demo`, `pilot`, nebo `production`
4. Telegram bot token a chat ID
5. OpenAI API key
6. typ mail klienta: `imap`, `gmail`, `graph`, nebo `helpdesk`
7. mailbox přístupy podle zvoleného klienta
8. cílové složky sorteru/responderu
9. zapnutí/vypnutí modulů
10. newsletter plán, pokud je newsletter zapnutý

### Po doběhnutí wizardu

Pro Railway:

```bash
railway status
# nahraj hodnoty z .env.railway do Railway variables
railway up --detach --message "Client launch"
railway deployment list
railway logs --lines 120
```

Pro lokální macOS launchd:

```bash
python3 scripts/install_launchd.py
tail -f logs/agent.log logs/agent_err.log
```

Nakonec otevři dashboard a ověř:

```text
/api/status
```

## Rychlá výměna klientského mailboxu

Pokud už instance běží nad testovacím mailboxem a u klienta chceš změnit jen
mailbox/provider hodnoty, použij menší wizard:

```bash
python3 scripts/mailbox_switch_wizard.py
```

Tenhle wizard:

- načte existující `.env`
- vytvoří zálohu `.env.before-mailbox-switch-YYYYMMDD-HHMMSS`
- má přesně 5 kroků:

| Krok | Co dělá |
|---|---|
| 1 | Zeptá se na typ mail klienta + IMAP host + SMTP host |
| 2 | Zeptá se na e-mail adresu / login |
| 3 | Zeptá se na IMAP heslo / app password, Enter ponechá stávající |
| 4 | Vypíše zbytek podle aktuální `.env`: porty, složky, moduly, `AUTO_RESPOND`, `DRY_RUN` |
| 5 | Zobrazí změny v tabulce, zapíše `.env` a nabídne propsání do Railway |
- vytvoří `MAILBOX_SWITCH_NEXT_STEPS.md`

Použij ho při schůzce, když je všechno ostatní připravené a mění se jen:

- testovací mailbox → klientský mailbox
- IMAP/SMTP přístupy
- cílové složky
- bezpečný pilot režim

## Jednoduchý průvodce

Pro založení konkrétní instance použij průvodce:

```bash
python3 scripts/new_instance_wizard.py
```

Průvodce se zeptá na hodnoty po jednotlivých krocích a zapíše je do `.env`.
Když nějakou hodnotu zatím neznáš, nech ji prázdnou; průvodce na konci vypíše,
kam přesně ji později doplnit.

### Otázky průvodce

1. **Název klienta / projektu**

   Příklad: `acme`

   Zapíše:

   ```env
   CLIENT_NAME=acme
   LAUNCHD_LABEL=com.mailagent.acme
   ```

2. **Dashboard port**

   Pokud poběží jen jedna instance, nech `8081`.
   Pokud běží víc instancí, použij další port, například `8082`.

   Zapíše:

   ```env
   DASHBOARD_PORT=8082
   ```

3. **Telegram**

   Zadáš:

   ```env
   TELEGRAM_BOT_TOKEN=
   TELEGRAM_CHAT_ID=
   ```

   Pokud hodnoty zatím nemáš, doplň je později do `.env`.

4. **OpenAI**

   Zadáš:

   ```env
   OPENAI_API_KEY=
   ```

5. **Mail klient**

   Vybereš `imap` nebo `gmail`.

   Pro IMAP doplníš:

   ```env
   MAIL_CLIENT=imap
   IMAP_HOST=
   IMAP_PORT=993
   IMAP_USER=
   IMAP_PASSWORD=
   SMTP_HOST=
   SMTP_PORT=587
   ```

   Pro Gmail doplníš:

   ```env
   MAIL_CLIENT=gmail
   GMAIL_ADDRESS=
   GMAIL_CREDENTIALS_FILE=credentials.json
   GMAIL_TOKEN_FILE=token.json
   ```

6. **Aktivní moduly**

   Zapíše:

   ```env
   MODULE_RESPONDER=true
   MODULE_SORTER=true
   MODULE_NEWSLETTER=false
   ```

7. **Bezpečný start**

   Výchozí bezpečné hodnoty:

   ```env
   DRY_RUN=true
   AUTO_RESPOND=false
   ```

   Produkční chování zapínej až po testu.

8. **Prompty**

   Průvodce hodnoty do promptů nedoplňuje automaticky. Po vytvoření `.env`
   uprav ručně:

   ```text
   prompts/classifier_prompt.txt
   prompts/response_A1.txt
   prompts/response_A2.txt
   prompts/response_A3.txt
   prompts/response_B1.txt
   prompts/response_B2.txt
   prompts/newsletter_format.md
   prompts/newsletter_queries.txt
   ```

   Knowledge base klienta ulož jako `.md` nebo `.txt` do `prompts/`.

## Ruční založení nové instance

```bash
cp -R mail-agent mail-agent-client-acme
cd mail-agent-client-acme
cp .env.example .env
```

V `.env` uprav:

```env
CLIENT_NAME=acme
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
OPENAI_API_KEY=
MAIL_CLIENT=imap
IMAP_HOST=
IMAP_USER=
IMAP_PASSWORD=
SMTP_HOST=
```

Lokální debug spuštění, jen když agent neběží přes launchd:

```bash
python3 main.py
```

macOS launchd instalace:

```bash
python3 scripts/install_launchd.py
```

Skript vygeneruje konkrétní plist z `launchd/com.mailagent.plist.template`,
dosadí aktuální `PROJECT_ROOT`, `LOG_DIR` a nainstaluje ho do
`~/Library/LaunchAgents`.

## Kontrola před předáním klientské instance

```bash
rg "/Users/lukas|mail-agent-venture|C:\\\\Users" .
```

Výsledek má být prázdný, nebo má ukazovat jen dokumentaci či template příklady.
Konkrétní lokální cesta smí vzniknout až při instalaci dané instance.
