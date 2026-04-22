# Architecture Decision Records (ADRs)

> Claude: před navrhováním nové technologie zkontroluj tento soubor.
> Pokud navrhovaná změna konfliktuje s rozhodnutím zde, upozorni Tommyho.

---

## ADR-001: Python jako primární jazyk

**Datum:** 2026-03-29
**Status:** Přijato

**Rozhodnutí:** Všechny projekty píšeme v Pythonu.

**Důvod:** Tommy programuje v Pythonu, ekosystém AI knihoven je v Pythonu nejsilnější (LangChain, ChromaDB, OpenAI SDK, atd.). Zbytečné přecházet na jiný jazyk.

**Vyhýbáme se:** Přepisu projektů do TypeScript/Node.js bez jasného důvodu.

---

## ADR-002: ChromaDB pro RAG projekty

**Datum:** 2026-03-29
**Status:** Přijato

**Rozhodnutí:** ChromaDB jako vector store pro RAG.

**Důvod:** Jednoduché lokální nasazení, žádné externí závislosti, funguje na Railway. Vhodné pro projekty této velikosti (~1000 dokumentů).

**Kdy zvážit alternativu:** Pokud projekt přesáhne ~100k dokumentů nebo potřebujeme multi-tenant → tehdy zvážit Pinecone nebo Weaviate.

---

## ADR-003: Railway pro deployment

**Datum:** 2026-03-29
**Status:** Přijato

**Rozhodnutí:** Railway jako primární deployment platforma.

**Důvod:** Jednoduchý deployment přes GitHub push, bez nutnosti DevOps znalostí. Vhodné pro portfoliové projekty.

**Alternativy zvažované:** Heroku (dražší), Render (podobné), VPS (složitější setup).

---

## ADR-004: OpenAI pro embeddings, Claude pro reasoning

**Datum:** 2026-03-29
**Status:** Přijato

**Rozhodnutí:** OpenAI `text-embedding-3-small` pro vektory, Claude pro složitější reasoning úkoly.

**Důvod:** OpenAI embeddings jsou stabilní a dobře integrované s ChromaDB. Claude je silnější v analyzování a plánování.

---

## ADR-005: Mail agent — Telegram jako potvrzovací a ovládací kanál

**Datum:** 2026-03-30
**Status:** Přijato

**Rozhodnutí:** Telegram bot slouží jako jediné rozhraní pro ovládání agenta — uvítací zpráva při startu, potvrzování odpovědí (/yes /no), manuální spuštění checku (/check).

**Chování při startu:** Agent pošle uvítací zprávu s popisem co monitoruje, interval checku a na jaké typy emailů reaguje.

**Příkazy:**

- `/check` — okamžitý check nových emailů
- `/yes` — schválí a odešle navrhovanou odpověď
- `/no` — přeskočí navrhovanou odpověď

**Důvod:** Tommy má zkušenost s Telegram boty, je to nejjednodušší interaktivní kanál bez nutnosti webového rozhraní.

---

## ADR-006: Tento repozitář je šablona pro více mail agent variant

**Datum:** 2026-04-13
**Status:** Přijato

**Rozhodnutí:** Repozitář nebude veden jen jako jednorázový Gmail agent, ale jako
základní template pro více typů mail agentů se společnou architekturou.

**Pevné části šablony:**

- Python orchestrace
- modulární vrstvy `classifier`, `responder`, `notifier`, `gmail_client`
- prompts jako hlavní konfigurovatelná vrstva chování
- project memory v `docs/project_notes/` a `tasks/`

**Proměnné části šablony:**

- intent taxonomy
- business pravidla
- datové integrace
- schvalovací workflow
- komunikační tón a brandové instrukce

**Důvod:** Chceme stavět více prezentovatelných agentů rychleji a konzistentně.
Společná kostra snižuje množství přepisovaného kódu a zároveň zachovává
čitelnost a nasaditelnost.

**Vyhýbáme se:** Vytváření každého nového mail agenta od nuly bez sdílené
struktury, dokumentace a opakovaně použitelného workflow.

---

## ADR-007: Zvážit one-shot spouštění agenta místo smyčky

**Datum:** 2026-04-20
**Status:** Otevřeno — k rozhodnutí

**Kontext:** Agent aktuálně běží jako dlouhodobý proces (smyčka + APScheduler). Tento přístup má opakující se problémy:

- `asyncio.Lock()` vytvořený mimo event loop → "Future attached to different loop"
- Vícenásobné spuštění (`run_polling()` + uvicorn thread) komplikuje správu event loopů
- Zaseknutí `/check` při souběhu více volání

**Navrhovaná alternativa:** Spouštět agenta jako **jednorázový skript každých 5 minut** (cron / Railway Cron Service):

- `python main.py` — načte emaily, zpracuje, ukončí se
- Telegram bot se spustí jen na dobu zpracování (nebo použít Telegram HTTP API přímo bez bota)
- Žádná smyčka → žádné problémy s event looopy, zamykáním, duplicitními instancemi

**Výhody:**

- Jednodušší kód — žádný APScheduler, žádný lock
- Přirozená idempotence — každé spuštění je nezávislé
- Snazší debugging — jeden run = jeden log

**Nevýhody:**

- `/yes` `/no` schvalování přes Telegram je složitější (musí čekat na odpověď mimo run)
- Telegram bot nepřijímá příkazy mezi spuštěními (jen v okně zpracování)

**Doporučení:** Zvážit při dalším refaktoru nebo při přechodu na produkci s vyšší zátěží.

---

## ADR-008: Railway provoz — worker + restart policy + timeouty

**Datum:** 2026-04-22
**Status:** Přijato jako krátkodobé produkční řešení

**Kontext:** Lokálně agent běží přes `launchd` s `KeepAlive`, ale na Railway
`launchd` neexistuje a ani není potřeba. Railway umí restartovat padlé procesy
vlastní restart policy. Jiný problém je zaseknutí procesu při práci s maily:
pokud proces pořád žije, běžná restart policy ho nemusí restartovat.

**Rozhodnutí pro krátkodobý provoz:**

- Na Railway běží jedna worker instance přes `Procfile`: `worker: python main.py`
- V Railway dashboardu nastavit restart policy na `Always`
- Nepoužívat `launchd`, cron ani paralelní `python main.py` instance
- Zaseknutí řešit primárně timeouty kolem externích operací:
  - IMAP connect/fetch/move
  - Gmail API
  - OpenAI API
  - Telegram send/poll
  - newsletter scraping

**Proč:** Telegram polling a approval flow potřebují dlouho běžící proces.
Worker + restart policy je nejmenší změna, která odpovídá současné architektuře.
Timeouty snižují riziko, že jeden zaseknutý request zablokuje celý check.

**Co to neřeší:** Pokud se Python proces zasekne tak, že pořád běží, ale už nedělá
užitečnou práci, Railway ho nemusí sama restartovat.

**Dlouhodobé řešení:** Přidat heartbeat a health endpoint:

- agent průběžně zapisuje čas poslední aktivity/checku
- `/api/health` vrací chybu, pokud heartbeat zestárne nebo check běží příliš dlouho
- Railway healthcheck restartuje kontejner při opakovaném selhání endpointu

**Alternativa:** One-shot režim přes Railway Cron Service. Ten je jednodušší proti
zaseknutí, ale hůř se kombinuje s Telegram `/yes` / `/no` approval flow.

---

## Šablona pro nové ADR

```markdown
## ADR-XXX: [Název]

**Datum:** YYYY-MM-DD
**Status:** Přijato

**Rozhodnutí:**

**Důvod:**

**Vyhýbáme se:**
```
