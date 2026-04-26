# Test: Cyklus Zrušit pravidlo / Přesunout do spamu

**Datum:** 2026-04-26
**Cíl:** Ověřit, že tlačítka "Zrušit pravidlo" a "Přesunout do spamu" fungují opakovaně
bez omezení počtu cyklů.

---

## Předpoklad

- Sorter přesunul nějaký email do spamu a uložil pravidlo (`from_address` nebo `content_hash`).
- Dashboard zobrazuje tento email jako **Přesunuto** s tlačítkem **Zrušit pravidlo**.

---

## Kroky

### Klik 1 — Zrušit pravidlo

1. Na dashboardu najdi email se stavem **Přesunuto** a tlačítkem **Zrušit pravidlo**.
2. Klikni **Zrušit pravidlo**.
3. Ověř:
   - Status bar zobrazí "Pravidlo zrušeno a email vrácen do inboxu."
   - Řádek se přepne na stav **Ponecháno**.
   - Tlačítko **Zrušit pravidlo** zmizí; místo něj se objeví **Jen tento typ** a **Vždy od odesílatele**.
   - Email se skutečně vrátil do INBOX (ověř v poštovním klientovi).

### Klik 2 — Přesunout zpět do spamu

4. Na stejném řádku klikni **Jen tento typ** (nebo **Vždy od odesílatele**).
5. Ověř:
   - Status bar zobrazí "Email přesunut. Naučeno jako ...".
   - Řádek se přepne na stav **Přesunuto** a přesune se na začátek seznamu.
   - Metoda je **Dashboard**.
   - Tlačítko **Zrušit pravidlo** se znovu objeví.
   - Email se skutečně přesunul do spamu (ověř v poštovním klientovi).

### Klik 3 — Zrušit pravidlo podruhé (ověření cyklu)

6. Klikni **Zrušit pravidlo** na tomto záznamu.
7. Ověř stejné výsledky jako v kroku 3.

### Opakování

Cyklus (kroky 4–7) musí být opakovatelný bez omezení.

---

## Co testujeme

| Problém                                      | Mechanismus                                                |
| -------------------------------------------- | ---------------------------------------------------------- |
| Po restore zůstával stav "Přesunuto"         | `_update_history_record_to_kept` přepisuje záznam in-place |
| Třetí klik selhal (email nenalezen ve spamu) | `move_kept_email_to_spam` hledá INBOX UID přes Message-ID  |
| Pravidlo se smazalo dřív než se email vrátil | Atomické pořadí: nejdřív přesun, pak smazání pravidla      |

---

## Očekávaný výsledek

Všechny tři kliky proběhnou bez chyby. Cyklus je nekonečně opakovatelný.
