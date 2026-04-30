# Test: Perzistence KEEP pravidel na Railway po redeploymentu

**Datum:** 2026-04-27
**Cíl:** Ověřit, že KEEP pravidlo vytvořené přes "Vrátit a vždy ponechat" přežije redeploy a je aktivně použito.

---

## Předpoklad: Railway Volume

Stejný předpoklad jako pro MOVE pravidla — `DATA_DIR` musí ukazovat na Railway Volume (`/data`), jinak data po restartu zmizí.

---

## Krok 1: Vytvoř KEEP pravidlo přes dashboard

V dashboardu najdi email v sorter historii s výsledkem **Přesunuto** (moved) — může být přesunut AI i pravidlem. Rozklikni řádek a klikni **"Vrátit a vždy ponechat"**.

Dashboard zobrazí potvrzení: _"Email vrácen do inboxu a odesílatel přidán do KEEP pravidel."_

## Krok 2: Ověř pravidlo v DB

Přes Railway CLI ověř přímo v DB:

```bash
railway run python3 -c "
import sqlite3
from src.config import DATA_DIR
conn = sqlite3.connect(DATA_DIR / 'sorter_rules.db')
rows = conn.execute(\"SELECT rule_type, rule_value, action FROM sorter_rules WHERE action='KEEP'\").fetchall()
print(rows)
"
```

**Úspěch:** výpis obsahuje řádek s `action='KEEP'` a `from_address` odesílatele

## Krok 3: Redeploy

```bash
railway up --detach --message "Test KEEP persistence"
railway deployment list  # počkej na SUCCESS
```

## Krok 4: Ověř funkčnost pravidla po restartu

Pošli testovací email ze stejné adresy odesílatele na inbox a spusť `/check` přes Telegram.

V dashboardu by měl přibýt nový záznam:

```
method:    Pravidlo
rule_type: from_address
outcome:   Ponecháno
```

**Úspěch:** `method: Pravidlo`, `outcome: kept` — KEEP pravidlo přežilo redeploy a bylo aktivně použito
**Selhání:** `method: AI` — pravidlo se nenačetlo, Volume pravděpodobně není připojený
