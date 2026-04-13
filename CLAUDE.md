# Projekty — Tommy

> Portfolio AI projektů: RAG vyhledávání, Telegram boti, asistenti pro trenéry a nutričníky.
> Cíl: funkční, nasazené aplikace vhodné do portfolia a pro demonstraci klientům.

---

## Stack

- **Jazyk:** Python (primární)
- **AI:** OpenAI API (GPT-4, embeddings), Anthropic API (Claude)
- **Vector DB:** ChromaDB (RAG projekty)
- **Deployment:** Railway + GitHub
- **Boti:** python-telegram-bot
- **Web:** jednoduchý HTML/JS frontend nebo Python webový server

---

## Konvence

- Komentáře a názvy proměnných: anglicky v kódu, čeština v komunikaci se mnou
- `.env` soubory pro všechny API klíče — nikdy je necommituj
- Každý projekt má vlastní `requirements.txt`
- Loguj přes `logging` modul, ne `print()` v produkci
- Preferuj jednoduchost — méně kódu, které funguje, nad složitostí, která nefunguje

---

## Stávající projekty

- **RAG citační vyhledávač** — Python + ChromaDB + ~1000 studií, nasazeno na Railway
- **Rohlik.cz Telegram bot** — automatické nákupy přes Telegram
- **Nutriční/tréninkový asistent** — ChatGPT s video transkripty, pro vztah trenér-klient
- **Mail Agent** — e-mailový agent pro Gmail, nasazeno na Railway

## Mail Agent — Infrastruktura

- **Railway token:** `e2b4b43c-b5c1-4ab8-9885-70d936782acc`
- **Railway Project ID:** `2e231bd5-5020-4327-8df5-e059f0fcbb8a`
- **Railway Service ID:** `814fa52b-18b6-4e3c-8127-85cbae48eb16`
- **GitHub:** `https://github.com/lukasv2255/mail-agent`
- **Gmail:** `newagent7878@gmail.com`
- **Telegram Chat ID:** `479991910`

---

## Cíl každého projektu

1. Musí fungovat a být nasazeno (Railway / GitHub)
2. Musí být prezentovatelné klientovi nebo zaměstnavateli
3. Kód musí být čitelný a pochopitelný i po měsíci

---

## Project Memory

Před každou prací zkontroluj:
- `docs/project_notes/key_facts.md` — API klíče, porty, endpointy, konfigurace
- `docs/project_notes/decisions.md` — co a proč jsme zvolili
- `docs/project_notes/bugs.md` — problémy které jsme už řešili
- `tasks/lessons.md` — co se neosvědčilo, co opakovat

Po každé opravě nebo poučení aktualizuj příslušný soubor.

---

## Task Management

- Netriviální úkol (3+ kroky) → nejdřív plan do `tasks/todo.md`
- Po každé korekci → přidej poučení do `tasks/lessons.md`
- Na začátku session → přečti `tasks/lessons.md`

---

## Komunikace

- Odpovídej česky
- Buď stručný — jeden správný příklad je lepší než tři alternativy
- Vysvětluj **proč**, nejen co — Tommy se učí, ne jen kopíruje
- Když něco nevíš nebo si nejsi jistý, řekni to
