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

## Šablona pro nové ADR

```markdown
## ADR-XXX: [Název]

**Datum:** YYYY-MM-DD
**Status:** Přijato

**Rozhodnutí:**

**Důvod:**

**Vyhýbáme se:**
```
