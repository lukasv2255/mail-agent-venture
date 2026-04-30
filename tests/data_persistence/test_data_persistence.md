# Test: Perzistence dat na Railway po redeploymentu

**Datum:** 2026-04-25
**Cíl:** Ověřit, že data uložená za běhu (pravidla, historie, stav) přežijí restart Railway deploymentu.

Platí pro všechny moduly, které zapisují do `DATA_DIR`:

- **sorter** — `sorter_rules.db` (pravidla přesunu)
- **responder** — (budoucí perzistentní stav)
- jakýkoli modul přidaný v budoucnu

---

## Předpoklad: Railway Volume

Aby data přežila redeploy, musí platit:

- `DATA_DIR` env var ukazuje na Railway Volume mount (např. `/data`)
- Volume je připojený k deploymentu v Railway dashboardu
- **Pokud Volume chybí**, data se zapisují do ephemeral `/app/data/` a po restartu zmizí

---

## Krok 0: Ověř, že DATA_DIR míří na Volume

Přes Railway CLI jednou před prvním testem:

```bash
railway run python3 -c "
from src.config import DATA_DIR
print('DATA_DIR:', DATA_DIR)
"
```

**Úspěch:** cesta začíná na `/data` (nebo jiný Volume mount point)
**Selhání:** cesta je `/app/data` — nastav `DATA_DIR=/data` v Railway env vars a připoj Volume

---

## Modul: sorter — pravidla přesunu

### 1. Vytvoř pravidlo přes dashboard

V dashboardu najdi email v sorter historii s výsledkem **Ponecháno** (kept) a klikni na
**"Přesunout — jen tento typ"** (rule_mode: `content` nebo `sender`).

> **Poznámka:** Endpoint `POST /api/sorter/move-to-spam` vyžaduje email s `outcome: kept`.
> Pokud jsou všechny emaily v historii `moved`, je potřeba nejdřív dostat nový email do
> inboxu, spustit `/check` přes Telegram, a teprve pak použít dashboard.

Po úspěšném přesunu dashboard zobrazí:

- Metoda: **Pravidlo**
- rule_type: `content_hash` nebo `from_address`
- outcome: **Přesunuto**

### 2. Ověř pravidlo v sorter historii

V dashboardu (`/api/sorter-history`) ověř, že přibyl záznam s:

```
method:    dashboard
rule_type: content_hash  (nebo from_address)
outcome:   moved
```

### 3. Redeploy + ověření přežití

```bash
railway up --detach --message "Test persistence"
railway deployment list  # počkej na SUCCESS
```

### 4. Ověř funkčnost pravidla po restartu

Přesuň testovací email zpět do inboxu (ručně v mailboxu) a spusť `/check` přes Telegram.

V dashboardu (`/api/sorter-history`) by měl přibýt nový záznam:

```
method:    Pravidlo   (ne AI)
rule_type: content_hash
outcome:   Přesunuto
```

**Úspěch:** `method: Pravidlo` — pravidlo přežilo redeploy a bylo aktivně použito
**Selhání:** `method: AI` — pravidlo se nenačetlo, Volume pravděpodobně není připojený

> **Ověřeno 2026-04-25:** Postup otestován end-to-end. Po připojení Railway Volume
> (`DATA_DIR=/data`) pravidlo typu `content_hash` přežilo redeploy a správně matchovalo
> email — dashboard zobrazil `method: Pravidlo`.

---

## Šablona pro nový modul

Při přidání nového modulu s perzistentními daty dopiš sekci podle stejné struktury:

1. **Vytvoř data** — jak (API endpoint / skript / akce uživatele)
2. **Ověř v DB / souboru** — jak zkontrolovat stav před restartem
3. **Redeploy + ověření přežití** — stejný příkaz, jiná tabulka/soubor
4. **Ověř funkčnost** — jak potvrdit, že data jsou aktivně využívána

Klíčové otázky pro nový modul:

- Kam přesně zapisuje? (soubor, SQLite tabulka, JSON)
- Cesta jde přes `DATA_DIR`? Pokud ne, oprav to.
- Inicializuje se cesta při importu nebo za běhu? (pozor na race condition s env vars)

---

## Možné příčiny selhání (obecně)

| Problém                               | Příčina                                             | Oprava                                               |
| ------------------------------------- | --------------------------------------------------- | ---------------------------------------------------- |
| Data chybí po restartu                | `DATA_DIR` míří do ephemeral `/app/...`             | Nastav Railway Volume a `DATA_DIR` env var           |
| Modul píše mimo `DATA_DIR`            | Hardcoded cesta v kódu                              | Oprav na `path_from_env(...)` z `src/config.py`      |
| Match / načtení nefunguje po restartu | Cesta se inicializuje při importu, dřív než env var | Zkontroluj pořadí importů a inicializace v `main.py` |
| Response 401                          | `DASHBOARD_TOKEN` nesedí                            | Zkontroluj Railway env vars                          |
