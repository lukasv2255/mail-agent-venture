# Issues — Otevřené problémy a kontext

> Přehled aktuálního stavu, otevřených problémů a věcí co je potřeba udělat.
> Claude: přečti před každou session abys pochopil kde projekt stojí.

---

## Aktuální stav projektu

Repo aktuálně obsahuje funkční referenční MVP mail agenta pro Gmail.
Agent umí:

- pravidelně kontrolovat inbox,
- klasifikovat email do základních kategorií,
- vygenerovat draft odpovědi,
- poslat návrh do Telegramu ke schválení,
- po schválení odpověď odeslat a email označit jako zpracovaný.

Aktuální rozšíření projektu:
- dokumentace se posouvá směrem k reusable template pro více mail agentů,
- vznikla univerzální support šablona a projektový blueprint pro další varianty.

---

## Otevřené problémy

### 2026-04-13 — Chybí formalizovaný blueprint pro nové agent varianty v kódu

**Popis:** Repo má společnou architekturu, ale zatím neobsahuje samostatnou
runtime konfiguraci nebo adresářovou strukturu pro více konkrétních agent variant.

**Priorita:** Střední

**Kontext:** Dokumentační základ už existuje, ale implementačně je stále přítomná
jedna konkrétní varianta s `type_a` a `type_b`.

**Blokuje:** Ne

### 2026-04-13 — Chybí testy pro klíčové moduly

**Popis:** Klasifikace, generování odpovědi a schvalovací flow nejsou pokryty testy.

**Priorita:** Vysoká

**Kontext:** Pro portfolio a další varianty agenta bude potřeba jistota, že se
společná kostra nerozbije při rozšiřování.

**Blokuje:** Částečně

### [Datum] — [Název problému]

**Popis:** Co nefunguje nebo chybí

**Priorita:** Kritická / Vysoká / Střední / Nízká

**Kontext:** Proč to existuje, co bylo zkoušeno

**Blokuje:** [Ano/Ne — co to blokuje]

---

## Nedávno dokončené

### 2026-04-13 — Support template a projektový základ pro více agentů

Byl vytvořen obecný support template dokument a repozitář byl popsán jako
základ pro více variant mail agentů.

---
