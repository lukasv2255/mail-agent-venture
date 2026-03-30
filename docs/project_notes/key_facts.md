# Key Facts — Klíčové konfigurace

> Claude: nehavluj konfigurace ani technologie — hledej zde.

---

## Stack

- **Jazyk:** Python 3.11+
- **AI APIs:** OpenAI (GPT-4, embeddings), Anthropic (Claude)
- **Vector DB:** ChromaDB
- **Deployment:** Railway (server), GitHub (verzování)
- **Boti:** python-telegram-bot
- **Frontend:** HTML/JS (jednoduché, bez frameworku)

## API klíče (vždy v .env, nikdy v kódu)

```
OPENAI_API_KEY=        # OpenAI GPT + embeddings
ANTHROPIC_API_KEY=     # Claude API
TELEGRAM_BOT_TOKEN=    # Telegram bot
```

## Nasazené projekty

| Projekt | URL | Platform |
|---|---|---|
| RAG citační vyhledávač | [doplnit Railway URL] | Railway |
| Rohlik bot | Telegram | Telegram |

## ChromaDB

- Lokální persistent storage: `./chroma_db/`
- Embedding model: `text-embedding-ada-002` (OpenAI) nebo `text-embedding-3-small`
- Collection: `[doplnit název kolekce]`
- Počet dokumentů: ~1000 studií

## Railway deployment

- Push na GitHub main → automatický deploy
- Env proměnné nastaveny přímo v Railway dashboardu (ne v .env souboru)
- `Procfile` nebo `railway.json` pro definici start příkazu

## Mail Agent — E-mailový agent

### Typy emailů
- **type_a** — zákazník se ptá na produkt (co dělá, jestli se jedná o správný výrobek)
- **type_b** — zákazník se ptá na stav objednávky (odesláno? kdy dorazí?)
- **unknown** — vše ostatní → agent neodpoví

### Testovací logika (dočasná, nahradit reálnými daty)
**type_a:**
- Produkt = elektronika → zamítnutí ("pletete si výrobek")
- Produkt = cokoli jiného → potvrzení ("ano, jedná se o správný produkt")

**type_b:**
- Číslo objednávky končí **lichým** číslem → odesláno, dorazí do 2 dnů + vygenerované tracking ID (formát: CZ + 9 číslic)
- Číslo objednávky končí **sudým** číslem → zatím neodesláno, v přípravě
- Číslo objednávky nenalezeno → požádej zákazníka o zopakování

### Testovací emaily (poslat z druhého účtu)
| # | Typ | Obsah | Očekávaná odpověď |
|---|-----|-------|-------------------|
| 1 | type_a | Dotaz na sportovní boty | Potvrzení |
| 2 | type_a | Dotaz na notebook | Zamítnutí |
| 3 | type_b | Objednávka č. 10473 (liché) | Odesláno + tracking ID |
| 4 | type_b | Objednávka č. 20884 (sudé) | V přípravě |
| 5 | unknown | Reklamace nebo stížnost | Žádná odpověď |

### Potvrzovací mechanismus (testovací režim)
- Agent pošle draft do Telegramu
- Čeká na `/yes` nebo `/no` (timeout 5 minut)
- `DRY_RUN=true` → pouze loguje, vůbec neposílá ani Telegram notifikaci

### Env proměnné
```
GMAIL_CREDENTIALS_FILE=credentials.json
GMAIL_TOKEN_FILE=token.json
GMAIL_ADDRESS=sledovany@gmail.com
ANTHROPIC_API_KEY=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
DRY_RUN=true
CHECK_INTERVAL_MINUTES=60
```

---

## Rohlik.cz bot

- Komunikace přes Telegram
- [Doplnit: jak funguje přihlášení na Rohlik]
- [Doplnit: co přesně bot umí — přidání do košíku? objednání?]
