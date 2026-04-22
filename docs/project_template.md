# Projektová šablona — Mail / Support Agent

> Technická osnova pro návrh nového mail nebo support agenta.
> Každý projekt vychází z této šablony — mění se jen business logika, kostra zůstává.
> Poslední aktualizace: 2026-04-22

---

## 1. Co je v každém projektu pevné (sdílená kostra)

### Kód

- `main.py` — vstupní bod, Telegram bot, scheduling, načítání modulů
- `src/classifier.py` — klasifikace typu e-mailu
- `src/notifier.py` — schvalovací kanál (výchozí: Telegram)

**Moduly — zapínat/vypínat per klient přes env proměnné:**

| Soubor                      | Env                      | Funkce                                       |
| --------------------------- | ------------------------ | -------------------------------------------- |
| `src/modules/responder.py`  | `MODULE_RESPONDER=true`  | Automatické odpovědi na příchozí emaily      |
| `src/modules/sorter.py`     | `MODULE_SORTER=true`     | Třídění inboxu — obchodní nabídky vs. zbytek |
| `src/modules/newsletter.py` | `MODULE_NEWSLETTER=true` | Tvorba a rozesílání newsletterů (TODO)       |

**Mail client — vybrat podle poskytovatele klienta:**

- `src/mail_client_gmail.py` — Gmail / Google Workspace (OAuth2)
- `src/mail_client_imap.py` — jakýkoliv e-mail (Seznam, vlastní server, firemní)
- `src/mail_client_graph.py` — Outlook / Office 365 (Microsoft Graph API)
- `src/mail_client_helpdesk.py` — Zendesk nebo Freshdesk (tiketovací systém)

Přepínání přes env: `MAIL_CLIENT=imap` — žádná změna kódu.

### Provozní standard

- env proměnné v `.env`, nikdy v kódu
- logování přes `logging` modul
- deployment na Railway přes GitHub push
- schválení odpovědí přes Telegram (`/yes` / `/no`)

### Projektová dokumentace

- `docs/key_facts.md` — konfigurace, API klíče, endpointy
- `docs/decisions.md` — architektonická rozhodnutí (ADR)
- `docs/bugs.md` — vyřešené bugy
- `docs/issues.md` — otevřené problémy
- `tasks/todo.md` — aktuální plán
- `tasks/lessons.md` — poučení ze session

---

## 2. Co se mění mezi projekty

### Intent model

- jaké typy e-mailů agent rozpoznává
- co je `unknown` (agent neodpovídá)
- priority a rizikovost jednotlivých typů

### Response policy

- co agent odešle automaticky
- co musí schválit člověk
- co se musí eskalovat (a kam)

### Business data

- produktový katalog
- objednávky a stav dopravy
- billing a faktury
- reklamace

### Komunikační styl

- tón odpovědi (formální / neformální)
- jazyk
- délka odpovědí
- podpis

### Schvalovací kanál

- Telegram (výchozí)
- shared inbox workflow
- jiný systém

Viz sekce 11 — přehled všech možností.

---

## 2A. Jak správně duplikovat projekt

Mail agent se nesmí duplikovat jen prostým zkopírováním složky. Každá nová varianta
musí dostat vlastní provozní identitu, jinak se snadno stane, že launchd spouští
jiný projekt, dashboard čte jiné logy, nebo editor ukazuje prázdný soubor ze staré
složky.

### Checklist po zkopírování repozitáře

1. **Nová složka projektu**

   Příklad:

   ```bash
   cp -R ~/claude-code/mail-agent ~/claude-code/mail-agent-venture
   ```

2. **Nový launchd label**

   Nepoužívat ve dvou projektech stejný label:

   ```text
   com.mailagent.agent
   ```

   Nová varianta má mít vlastní label, například:

   ```text
   com.mailagent.venture
   ```

3. **Nový plist název**

   Příklad:

   ```text
   launchd/com.mailagent.venture.plist
   ~/Library/LaunchAgents/com.mailagent.venture.plist
   ```

4. **Přepsat absolutní cesty v plist**

   Zkontrolovat hlavně:

   - `WorkingDirectory`
   - `StandardOutPath`
   - `StandardErrorPath`

   Všechny musí mířit na novou složku projektu, ne na původní projekt.

5. **Oddělit `.env`**

   Nový projekt má vlastní `.env`. Telegram token, chat ID, mailbox a API klíče
   mohou být stejné jen pokud je to záměr. Nikdy nepřebírat citlivé hodnoty z
   oříznutého výstupu CLI.

6. **Oddělit logy**

   Dashboard sorteru čte:

   ```text
   logs/sorter/sorter.jsonl
   ```

   Pozor na stejné relativní cesty ve dvou různých projektech:

   ```text
   ~/claude-code/mail-agent/logs/sorter/sorter.jsonl
   ~/claude-code/mail-agent-venture/logs/sorter/sorter.jsonl
   ```

   V editoru vždy ověřit absolutní cestu, ne jen název tabu.

7. **Načíst správnou launchd službu**

   Příklad:

   ```bash
   cp launchd/com.mailagent.venture.plist ~/Library/LaunchAgents/com.mailagent.venture.plist
   launchctl bootstrap gui/501 ~/Library/LaunchAgents/com.mailagent.venture.plist
   launchctl kickstart -k gui/501/com.mailagent.venture
   ```

8. **Ověřit co skutečně běží**

   ```bash
   launchctl print gui/501/com.mailagent.venture
   tail -n 20 logs/agent.log
   tail -n 20 logs/sorter/sorter.jsonl
   ```

### Pravidlo

Nový mail agent = nová složka, nový launchd label, nový plist název, nové log cesty
a zkontrolovaný `.env`. Jedna stará absolutní cesta stačí k tomu, aby běžela správná
služba nad špatným projektem.

---

## 3. Typy mailových systémů (kde agent může fungovat)

### Osobní mailbox (Gmail / Outlook)

- freelancer nebo malá firma
- 1–3 lidé odpovídají ručně
- vhodné pro MVP a "draft reply assistant"

### Shared inbox (`support@`, `info@`)

- více lidí pracuje nad jednou adresou
- potřeba přehledu kdo co řeší
- nejlepší vstupní bod pro první reálný support agent

### Helpdesk / ticketing (Zendesk, Freshdesk)

- střední a větší firmy
- e-mail → tiket s číslem, stavem, přiřazením
- vhodné pro robustní automatizaci s triage a routingem

### CRM / ERP napojený support

- odpověď závisí na datech: objednávka, sklad, platba, historie zákazníka
- nejvyšší business hodnota, nejvyšší nároky na integrace

---

## 4. Oblasti které support typicky řeší

### Pre-sales

- je to správný produkt?
- jaké má parametry / je kompatibilní s X?
- máte to skladem?

### Order support

- kde je moje objednávka?
- byla odeslána? kdy dorazí?
- změna adresy nebo položky
- storno

### Post-sales

- vrácení zboží
- reklamace, poškozená zásilka
- chybějící položka

### Billing

- faktura, kopie dokladu
- platba nepřišla / duplicitní platba
- změna fakturačních údajů

### Výjimečné případy (vždy člověk)

- stížnost, VIP zákazník
- právní dotaz, GDPR žádost
- eskalace na manažera

---

## 5. Rozhodovací vrstvy agenta

```
1. Intake       — převzetí e-mailu
2. Classification — typ, priorita, riziko
3. Enrichment   — doplnění dat (objednávka, produkt...)
4. Policy check — co smí agent udělat sám
5. Response     — návrh odpovědi
6. Approval     — člověk schvaluje nebo agent odesílá sám
7. Logging      — uložení výsledku a metrik
```

---

## 6. Co agent potřebuje jako vstupy

### Z e-mailu

- předmět, tělo zprávy, odesílatel
- historie vlákna
- jazyk

### Z business systémů

- číslo objednávky a její stav
- sledování zásilky
- stav platby
- produktová data a FAQ

### Z konfigurace

- pravidla eskalace a klíčová slova
- tón a šablony odpovědí
- SLA (garantovaná doba odpovědi)
- seznam zakázaných akcí

---

## 7. Eskalační triggery — klíčová slova

```python
ESCALATE_KEYWORDS = [
    "advokát", "soud", "GDPR", "ochrana osobních údajů",
    "nikdy více", "skandál", "sociální sítě", "novinář",
    "podvod", "krádež", "urgentní", "okamžitě",
    "cancel", "churn", "výpověď smlouvy",
    "neakceptovatelné", "nepřijatelné"
]
```

---

## 8. Šablona zadání pro nový projekt

Při zakládání nové varianty vyplnit:

```
### Kontext firmy
- Segment: (e-shop / SaaS / servisní / jiné)
- Velikost: (počet lidí, objem e-mailů za den)
- Hlavní problém, který agent řeší:

### Systémy
- Mail systém:
- Helpdesk (pokud existuje):
- CRM / ERP / OMS:
- Knowledge base:

### Typy e-mailů (top 5–10)
- intent 1 — auto / human / escalate
- intent 2 — auto / human / escalate
- ...

### Automatizační hranice
- Agent smí poslat sám: ...
- Musí schválit člověk: ...
- Nesmí se automatizovat: ...

### Data
- Zdroj pravdivých dat: ...
- Co udělat při chybějících datech: ...

### Komunikační styl
- Tón: (formální / neformální)
- Jazyk:
- Podpis:

### Měření úspěchu
- Cílová míra automatizace:
- Max. čas odpovědi:
- Míra eskalace:
```

---

## 9. Minimální checklist pro novou variantu

- [ ] Definovat nové intenty (typy e-mailů)
- [ ] Napsat nebo upravit prompty
- [ ] Určit zdroj dat pro odpovědi
- [ ] Nastavit pravidla schválení a eskalace
- [ ] Popsat edge cases a `unknown`
- [ ] Připravit testovací e-maily
- [ ] Ověřit Railway-ready konfiguraci (Procfile, env vars)

---

## 10. Varianty agenta vhodné pro toto repo

**Draft assistant** — Nízká složitost
Navrhuje odpovědi, člověk vždy schvaluje. Nejbezpečnější varianta pro start.

**Order status agent** — Střední složitost
Odpovídá na dotazy o stavu objednávky. Vyžaduje napojení na data objednávek.

**Product FAQ agent** — Střední složitost
Odpovídá na pre-sales dotazy z produktového katalogu nebo knowledge base.

**Returns / complaint triage** — Střední složitost
Třídí reklamace a vrácení zboží. Většinu předává člověku, jednoduché případy řeší sám.

**Omnichannel router** — Vysoká složitost
Sjednocuje e-mail a další kanály (chat, WhatsApp). Rozhoduje o prioritě a cílovém týmu.

---

## 11. Varianty schvalovacího kanálu (notifier)

Jak agent oznamuje návrh odpovědi a čeká na schválení člověka.

**Telegram**
Bot pošle zprávu, člověk odpoví `/yes` nebo `/no`.

- Rychlé, zdarma, snadná implementace
  − Vyžaduje Telegram účet
  → Vhodné pro: vývojáře, osobní projekty

**Slack**
Bot v kanálu, nativní tlačítka Schválit / Zamítnout.

- Firmy Slack znají, hezké UI s tlačítky
  − Placený pro větší týmy
  → Vhodné pro: firemní nasazení

**Web dashboard**
Stránka s frontou čekajících e-mailů, schválení kliknutím.

- Nejprezentovatelnejší, zákazník nepotřebuje nic instalovat
  − Vyžaduje webový server (FastAPI)
  → Vhodné pro: prezentace klientovi, produkce

**E-mail**
Agent pošle draft e-mailem, člověk odpoví `yes` nebo `no`.

- Nulové závislosti navíc
  − Pomalé, nepohodlné
  → Vhodné pro: záloha, nejjednodušší MVP

**WhatsApp**
Přes Twilio API, stejná logika jako Telegram.

- Zákazníci ho znají lépe než Telegram
  − Twilio stojí peníze
  → Vhodné pro: klientská řešení

**Pushover / Ntfy**
Mobilní notifikace s tlačítky schválit / zamítnout.

- Jednoduché, rychlé nastavení
  − Omezené možnosti, málo známé
  → Vhodné pro: osobní použití

**Žádné schválení (auto-send)**
Agent odesílá low-risk odpovědi rovnou bez čekání.

- Nejrychlejší, plná automatizace
  − Vyžaduje přesnou klasifikaci rizika
  → Vhodné pro: produkce s prověřenou logikou

---

### Telegram — known issues a řešení

**ESC a UNK zprávy mohou zapadnout v chatu**
Drafty ke schválení, ESC upozornění a UNK notifikace přicházejí do jednoho chatu a mohou se promíchat.
→ Řešení: ESC a UNK zprávy se automaticky připnou (`pin_chat_message`) — zůstanou viditelné nahoře dokud je klient ručně neodepne.

**Timeout schválení**
Klient může být nedostupný celý den — původní 5 minutový timeout způsoboval tiché přeskočení emailu.
→ Řešení: timeout nastaven na 1 hodinu. Po vypršení agent pošle Telegram upozornění a email **neoznačí jako zpracovaný** — zpracuje se při příštím `/check`. `/no` stále označí email jako vyřízený (vědomé zamítnutí).

---

### Doporučení podle situace

- **Vývoj a testování** → Telegram
- **Prezentace klientovi** → Web dashboard
- **Produkce** → auto-send pro low-risk + Telegram nebo Slack pro citlivé typy
- **Firemní nasazení** → Slack nebo web dashboard

---

## 12. Typy e-mailových systémů a technický přístup

Před zahájením projektu zjistit: **jaký e-mailový systém klient používá.** Od toho se odvíjí celá implementace `mail_client.py`.

---

**IMAP**
Univerzální protokol podporovaný každým poskytovatelem (Gmail, Seznam, Centrum, vlastní server).

- Knihovna: `imaplib` (stdlib) nebo `imapclient`
- Autentizace: heslo nebo OAuth2 (Gmail a Outlook vyžadují OAuth2)
- Umí: číst, označovat, přesouvat, mazat
- Kdy použít: klient má firemní nebo libovolný e-mail mimo Google/Microsoft

**Gmail API**
Google REST API, nejrobustnější přístup pro Gmail.

- Knihovna: `google-api-python-client`
- Autentizace: OAuth2 (`credentials.json` + `token.json`)
- Umí: vše co IMAP + labely, vlákna, drafty, Pub/Sub webhooky
- Kdy použít: klient používá Gmail nebo Google Workspace
- Pozor: credentials.json nelze commitnout, musí být v Railway jako env proměnná nebo secret

**Microsoft Graph API**
REST API pro Outlook a Office 365.

- Knihovna: `requests` nebo `msgraph-sdk`
- Autentizace: OAuth2 přes Azure app registration
- Umí: číst, posílat, pracovat s kalendářem a kontakty
- Kdy použít: klient používá Outlook nebo firemní Office 365

**SMTP**
Pouze odesílání, žádné čtení.

- Knihovna: `smtplib` (stdlib)
- Autentizace: heslo nebo OAuth2
- Kdy použít: jako doplněk k IMAP nebo Gmail API pro odesílání odpovědí

**Helpdesk API (Zendesk, Freshdesk, Intercom)**
Nepracuješ s e-mailem přímo — pracuješ s tikety přes REST API.

- Knihovna: `requests` + API klíč
- Autentizace: API klíč v hlavičce
- Umí: číst tikety, přidávat komentáře, měnit stav, přiřazovat
- Kdy použít: klient má helpdesk systém místo klasického e-mailu

**Webhook (event-driven)**
Platforma pošle HTTP POST při každém novém e-mailu — žádný polling.

- Implementace: FastAPI endpoint přijímá události
- Podporuje: Gmail Pub/Sub, Sendgrid Inbound Parse, Mailgun, Postmark
- Kdy použít: klient chce real-time zpracování, velký objem zpráv

---

### Jak zjistit co klient používá

```
1. Jakou e-mailovou adresu support používá?
   → @gmail.com nebo @googleworkspace → Gmail API
   → @outlook.com nebo @firma.cz (Office 365) → Microsoft Graph
   → vlastní doména na jiném serveru → IMAP

2. Používají helpdesk? (Zendesk, Freshdesk...)
   → ano → Helpdesk API, e-mail jde přes něj

3. Jaký objem e-mailů denně?
   → do ~100 → polling každých N minut stačí
   → více → zvážit webhook
```

### Doporučení pro šablonu

Kód rozdělit tak, aby `mail_client.py` byl jediný soubor který se mění mezi projekty. Zbytek (classifier, responder, notifier) zůstává stejný.

```
src/
  mail_client_gmail.py       ← Gmail API
  mail_client_imap.py        ← IMAP (univerzální)
  mail_client_graph.py       ← Microsoft Graph
  mail_client_helpdesk.py    ← Zendesk / Freshdesk
```

Všechny implementují stejné rozhraní:

- `get_unprocessed_emails()`
- `mark_as_processed(email_id)`
- `send_reply(email, text)`

---

## 13. Kdo provozuje agenta — deployment model a bezpečnost

### Dva modely nasazení

**Model A — vývojář provozuje za klienta**
Agent běží na vývojářově Railway účtu, přistupuje ke klientově e-mailu.

- Klient dá přístup přes OAuth consent nebo API token
- Vývojář vidí obsah zpráv zákazníků klienta
- Při úniku dat nese odpovědnost vývojář
- Vhodné pro: testování, portfolio, MVP demonstrace

**Model B — klient provozuje sám**
Vývojář dodá kód, klient si nasadí na vlastní Railway nebo server.

- Klient má plnou kontrolu nad daty
- Vývojář nevidí žádné e-maily ani zákaznická data
- Správný model pro reálné produkční nasazení

---

### Bezpečnostní pravidla

**API klíče a credentials**

- Vždy v Railway env proměnných — nikdy v kódu ani v repozitáři
- Gmail `credentials.json` a `token.json` nesmí být commitnuty na GitHub
- Na Railway předat jako base64 env proměnnou (`GMAIL_TOKEN_JSON`)

**Schválení odpovědí**

- Vždy začít s `DRY_RUN=true` a approval flow (`/yes` / `/no`)
- `auto-send` zapnout až po ověření na reálných datech
- Pro citlivé typy e-mailů ponechat schválení trvale

**Logování**

- Logovat: předmět, odesílatel, typ e-mailu, výsledek
- Nelogovat: celé tělo zprávy — může obsahovat osobní údaje zákazníků
- Logy rotovat nebo mazat podle dohodnuté retenční doby

**GDPR**

- Agent zpracovává osobní údaje zákazníků klienta → vývojář je zpracovatel
- Klient musí mít s vývojářem zpracovatelskou smlouvu (DPA)
- Tohle řeší smluvní vztah, ne kód — ale je potřeba na to myslet před podpisem

---

### Checklist před předáním klientovi

- [ ] Kód neobsahuje žádné hardcoded klíče ani tokeny
- [ ] `.gitignore` obsahuje `.env`, `credentials.json`, `token.json`
- [ ] README vysvětluje jak nastavit env proměnné
- [ ] `DRY_RUN=true` jako výchozí hodnota
- [ ] Logování neukládá citlivý obsah e-mailů
- [ ] Klient ví že musí provozovat na svém účtu (Model B)

---

## 14. Knowledge Base — čím víc firma ví, tím líp agent odpovídá

Agent je tak dobrý jako informace které má k dispozici. Pokud firma dodá kvalitní KB, agent zvládne odpovědět i na složité dotazy bez eskalace.

### Co patří do KB

- Produktový katalog (složení, parametry, kompatibilita, kontraindikace)
- FAQ — nejčastější dotazy s ideálními odpověďmi
- Ceník, podmínky, reklamační řád
- Interní procesy (jak se vyřizuje objednávka, kdo co řeší)
- Tone of voice a zakázaná témata

### Dva přístupy podle velikosti KB

**Textové soubory v `prompts/`** — do ~50 stran textu
Agent dostane celou KB přímo do promptu. Jednoduché, žádná extra infrastruktura. Vhodné pro většinu malých firem.

> `prompts/` = produkční data pro konkrétní nasazení (prázdné dokud není reálný klient).
> `tests/` = vše testovací — KB, testovací emaily, prompty, fixtures — i pro budoucí projekty.
> Při nasazení pro klienta se soubory z `tests/projekt_XX/` zkopírují a upraví do `prompts/`.

**RAG s ChromaDB** — pro velké KB (stovky dokumentů)
Agent vyhledá jen relevantní části, ne celý dokument. Projekt má zkušenosti z RAG citačního vyhledávače — stejný přístup.

### Praktický dopad

Bez KB: dotaz _"Je váš protein vhodný pro diabetiky?"_ → eskalace.
S KB: agent vyhledá složení, kontraindikace, FAQ → odpověď bez zásahu člověka.

### KB adapter — přepínání zdroje dat

Klient může mít data v existující databázi (katalog produktů, objednávky) a při ostrém nasazení chce aby agent četl přímo odtud, ne ze souborů.

Řešení: agent nikdy nepracuje se zdrojem dat přímo — volá abstraktní funkci `get_kb()` a `kb_loader.py` rozhoduje odkud data přijdou.

```python
# src/kb_loader.py
import os

KB_SOURCE = os.getenv("KB_SOURCE", "file")  # "file" nebo "db"

def get_products():
    if KB_SOURCE == "file":
        return _load_from_file("prompts/kb_produkty.md")
    elif KB_SOURCE == "db":
        return _load_from_db()

def _load_from_file(path):
    with open(path, encoding="utf-8") as f:
        return f.read()

def _load_from_db():
    import psycopg2
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    # SELECT * FROM produkty WHERE aktivni = true
    ...
```

| Fáze      | `KB_SOURCE` | Data                                |
| --------- | ----------- | ----------------------------------- |
| Demo      | `file`      | vymyšlená KB v `tests/`             |
| Integrace | `db`        | klient dá přístup k DB, napíšeš SQL |
| Produkce  | `db`        | živá data klienta                   |

Výhoda: `classifier.py` a `responder.py` se nemění. Přibývá jen `_load_from_db()` až klient dá přístup.

---

## 15. Učení agenta — od zaměstnanců i z vlastních odpovědí

Agent se může zlepšovat dvěma způsoby.

### Explicitní učení — zaměstnanci učí tipy a triky

Zaměstnanec může agentovi předat pravidlo nebo tip přímo přes schvalovací kanál.

**Příkaz `/learn`:**

```
/learn Zákazníkům kteří se ptají na protein a zmiňují diabetes vždy doporučit konzultaci s lékařem a přidat odkaz na FAQ.
```

Agent uloží tip do KB (`prompts/tips.md`) a příště ho použije automaticky.

Podobně pro opravy tónu:

```
/learn Nepoužívat slovo "bohužel" — působí negativně. Nahradit neutrální formulací.
```

### Implicitní učení — z historii schválení a zamítnutí

Agent sleduje vzory ze schvalovacího flow:

- `/yes` na draft → odpověď byla dobrá, uložit jako vzor pro podobné e-maily
- `/no` + opravená verze od klienta → agent porovná svůj draft s opravou a zaznamená rozdíl
- Opakované zamítání stejného typu → agent sníží sebedůvěru pro daný typ, začne častěji žádat o schválení

**Kde se ukládají vzory:**

```
prompts/
  tips.md          ← manuální tipy od zaměstnanců (/learn)
  approved/        ← příklady schválených odpovědí podle typu
  corrections.md   ← záznamy oprav (co agent napsal vs. co klient chtěl)
```

### Limity

- Agent se neučí sám přepisovat pravidla klasifikace — to dělá vývojář
- Tipy a vzory se dají kdykoliv smazat nebo upravit
- Učení funguje v rámci projektu — každý klient má vlastní KB a vlastní historii

---

## 16. Živé demo před podpisem smlouvy

Klient chce vidět reálný průběh — přišel e-mail, přišla odpověď — ale nechce dát přístup ke svému inboxu ani datům.

**Řešení:** použij vlastní testovací inbox (např. `newagent7878@gmail.com`). Agent ho monitoruje přes Gmail API, KB je naplněná simulovanými daty klienta.

```
Klient pošle e-mail na testovací adresu
  → agent přečte, klasifikuje, vygeneruje odpověď z KB
  → Telegram: návrh odpovědi ke schválení (/yes / /no)
  → agent odešle odpověď zpět klientovi
```

Klient může sledovat Telegram skupinu kde agent posílá návrhy — vidí přesně co agent "vidí" a jak rozhoduje.

**Co připravit:**

- KB s vymyšlenými daty klienta v `prompts/`
- Agent běžící lokálně nebo na Railway
- Klient ví na jakou adresu psát

---

## 17. Shadow mode — testování paralelně vedle reálného supportu

Než agent začne odpovídat zákazníkům ostře, klient ho může testovat vedle sebe bez rizika.

### Jak funguje

Agent běží normálně — čte poštu, klasifikuje, generuje drafty, posílá ke schválení. Ale odesílání zákazníkovi je vypnuté. Zaměstnanec mezitím odpovídá ručně jako dřív.

Výsledek: klient vidí co by agent napsal, porovná s vlastní odpovědí, dá zpětnou vazbu.

```
DRY_RUN=false   ← agent generuje drafty a posílá ke schválení
SEND_ENABLED=false  ← ale reálně zákazníkovi neposílá
```

Nebo jednoduše: klient schvaluje `/yes` ale agent loguje místo odesílání — totéž co `DRY_RUN`, ale s Telegram notifikacemi aktivními.

### Doporučený postup nasazení

```
Fáze 1 — DRY_RUN=true      Agent jen loguje, žádné Telegram notifikace
Fáze 2 — Shadow mode        Agent posílá drafty ke schválení, zákazník nedostane nic
Fáze 3 — Postupné zapínání  Nejdřív nejjednodušší typy (stav objednávky, FAQ)
Fáze 4 — Plný provoz        Všechny schválené typy jdou automaticky nebo přes approval
```

### Metriky ze shadow mode

Po 2 týdnech shadow mode vyhodnotit:

- Kolik % draftů by bylo schváleno beze změny?
- Které typy e-mailů agent zvládá dobře vs. kde se mýlí?
- Jak rychle agent odpověděl vs. jak rychle zaměstnanec?
- Kolik eskalací bylo oprávněných?

Tato data určí které typy jsou připraveny na ostré odesílání a které potřebují ladění.
