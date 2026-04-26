# Railway Deploy

Tento projekt `mail-agent` nasazujeme na Railway primárně z lokálního checkoutu
přes Railway CLI. Nebereme jako hlavní workflow "push na GitHub main ->
automatický deploy", protože pro klientské instance je důležité nejdřív ověřit
správný Railway link, env proměnné a stav konkrétní služby.

## Doporučený workflow

1. Připrav nebo aktualizuj lokální konfiguraci:

```bash
python3 scripts/client_instance_wizard.py
```

Wizard vytvoří:

- `.env` pro lokální/runtime běh
- `.env.railway` pro Railway variables
- `NEXT_STEPS.md` bez tajných hodnot

2. Ověř, že checkout míří na správný Railway project a service:

```bash
railway status
```

Pokud link nesedí, přepoj ho přes `railway link`.

3. Nahraj hodnoty z `.env.railway` do Railway Variables.

Citlivé hodnoty necommituj. `.env` ani `.env.railway` nepatří do gitu.

4. Přidej persistentní Volume pro data (pravidla sorteru, stav agenta):

   Railway dashboard → service → **Volumes → Add Volume → Mount Path: `/data`**

   Pak nastav env proměnnou:

   ```bash
   railway variables set DATA_DIR=/data
   ```

   Bez Volume se data ztratí při každém redeploymentu.

5. Nasaď aktuální checkout:

```bash
railway up --detach --message "Client launch"
```

6. Ověř deploy a logy:

```bash
railway deployment list
railway logs --lines 120
```

7. Otevři veřejný dashboard a zkontroluj:

```text
/
/api/status
```

## Co Railway spouští

Start příkaz je definovaný v [Procfile](/Users/lukas/claude-code/mail-agent/Procfile:1):

```text
web: python main.py
```

`main.py` spouští agenta i web dashboard. Na Railway má prioritu env proměnná
`PORT`; lokálně se dashboard opírá o `DASHBOARD_PORT`.

## Railway-specific poznámky

- V Railway nepoužíváme `launchd`.
- Restart policy nastav na `Always`.
- `DATA_DIR` musí mířit na persistent Volume (`/data`), jinak se pravidla
  sorteru a stav agenta ztratí při každém redeploymentu. Viz krok 4 výše.
- Po změně env proměnných udělej nový deploy, aby běžel proces s aktuální
  konfigurací.

## Rychlý checklist

- `railway status` ukazuje správný project/service
- Railway Variables odpovídají `.env.railway`
- Volume je připojený, mount path `/data`, `DATA_DIR=/data` nastaveno
- deploy proběhl přes `railway up --detach`
- `railway logs --lines 120` neukazují startup chybu
- dashboard a `/api/status` vrací očekávaný stav
