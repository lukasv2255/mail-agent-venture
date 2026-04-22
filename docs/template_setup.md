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

## Interaktivní průvodce

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
