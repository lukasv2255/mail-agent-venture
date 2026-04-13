# Lessons — Naučené poučení

> Claude: přečti tento soubor na začátku každé session.
> Po každé korekci nebo chybě přidej poučení sem.

---

## Obecné principy práce s Tommym

- Tommy se **učí**, nejen kopíruje — vždy vysvětli proč, nejen co
- Preferuje **jedno správné řešení** před výběrem z pěti možností
- Rychle pochopí koncepty — nemusíš vysvětlovat základy Pythonu
- Cílí na **nasazené, prezentovatelné projekty** — vyhni se over-engineeringu
- Komunikace česky

## 2026-03-30 — Testovat sám, nežádat uživatele

**Situace:** Po každé drobné úpravě kódu Claude žádal Tommyho aby otestoval sám.

**Chyba:** Přehazování zodpovědnosti za testování na uživatele.

**Správně:** Po drobné úpravě napsat "Testuji přidání X..." a spustit test sám. Reportovat výsledek.

**Pravidlo:** Drobné změny vždy otestuj sám a reportuj výsledek — nereferuj uživatele.

---

## 2026-04-13 — Šablony ukotvovat do projektové memory

**Situace:** Vznikal obecný podklad pro support use-cases, ale uživatel upřesnil,
že výstup má sloužit jako šablona přímo pro tento projekt a jeho další mail agenty.

**Chyba:** Příliš obecný dokument bez pevného napojení na `CLAUDE.md`,
`docs/project_notes/` a `tasks/`.

**Správně:** Když se staví reusable template, ukotvit ji do existující projektové
struktury, decisions a key facts, ne jen do samostatného dokumentu.

**Pravidlo:** Obecný návrh vždy převeď do místní projektové memory a repové šablony.

---

## Šablona záznamu

```markdown
## [Datum] — [Název poučení]

**Situace:** Co se stalo

**Chyba:** Co bylo špatně nebo co nefungovalo

**Správně:** Jak to dělat příště

**Pravidlo:** [Jednořádkové shrnutí]
```

---
