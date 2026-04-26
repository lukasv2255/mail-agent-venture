# Test: zpětné aplikování pravidla na dříve ponechané emaily

**Datum:** 2026-04-26
**Cíl:** Ověřit, že po vytvoření pravidla `from_address` sorter při dalším průchodu
přesune i emaily které už jednou zpracoval jako "Ponecháno".

---

## Kontext

Dříve sorter přeskakoval všechny emaily které měl v historii — včetně `kept`.
To znamenalo, že pravidlo vytvořené přes dashboard platilo jen pro nové emaily,
ne pro 70 existujících v INBOX od stejného odesílatele.

Oprava: skip se aplikuje jen na `outcome=moved`. Emaily s `outcome=kept`
jsou při dalším průchodu znovu vyhodnoceny, pravidla se aplikují.

---

## Příprava

**Před spuštěním:** Ověř, že v `sorter_rules.db` neexistuje pravidlo `from_address`
pro odesílatele (Gmail účet agenta). Pokud existuje z předchozího testování,
emaily půjdou rovnou do Přesunuto a test nekrokuje správně — pravidlo nejdřív zruš
přes dashboard (Zrušit pravidlo) nebo přes DB.

```bash
python3 tests/sorter/test_rule_reapply.py
```

Skript odešle 3 emaily od stejného (testovacího) odesílatele na inbox agenta.

---

## Kroky

### Krok 1 — první průchod sorteru

1. Počkej až agent automaticky zpracuje emaily, nebo spusť `/sort` v Telegramu.
2. Ověř v dashboardu (sekce Sorter): 3 emaily od odesílatele `newagent7878@gmail.com`
   se subjekty `[reapply-test] ...` mají stav **Ponecháno**.

### Krok 2 — vytvoření pravidla

3. Klikni na jeden z těchto emailů v dashboardu.
4. Klikni **Vždy od odesílatele**.
5. Ověř: tento jeden email se přepnul na **Přesunuto**, pravidlo vzniklo.

### Krok 3 — zpětné aplikování

6. Spusť `/sort` v Telegramu (nebo počkej na automatický průchod).
7. Ověř v dashboardu: **všechny 3 emaily** mají stav **Přesunuto**.
8. Ověř v poštovním klientovi: emaily jsou ve spam složce.

---

## Očekávaný výsledek

Po druhém průchodu sorteru jsou všechny 3 emaily přesunuty — včetně těch
které byly při prvním průchodu ponechány.

## Co by selhalo před opravou

Emaily 2 a 3 by zůstaly jako **Ponecháno** protože sorter by je přeskočil
(`email_key` byl v historii bez ohledu na outcome).
