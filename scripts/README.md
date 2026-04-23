# scripts/

Pomocné skripty pro přípravu a provoz konkrétní instance. Nespouštějí se
automaticky, pouštějí se ručně z rootu projektu.

| Soubor | Popis |
| --- | --- |
| `client_instance_wizard.py` | Finální průvodce pro novou klientskou instanci. Vytvoří `.env`, `.env.railway` a `NEXT_STEPS.md`. |
| `mailbox_switch_wizard.py` | Průvodce pro přepnutí existující instance z testovací schránky na klientskou. Zálohuje `.env`, upraví mailové hodnoty a volitelně je propíše do Railway. |
| `install_launchd.py` | Vyrenderuje a nainstaluje macOS LaunchAgent plist pro aktuální instanci podle `.env`. |

## Doporučený postup

1. Zkopíruj šablonu projektu pro konkrétního klienta.
2. Spusť `python3 scripts/client_instance_wizard.py`.
3. Zkontroluj vygenerovaný `NEXT_STEPS.md`.
4. Pro lokální dlouhodobý běh na macOS spusť `python3 scripts/install_launchd.py`.

Pokud už instance běží na testovací schránce a má se přepnout na klientskou,
spusť místo vytváření nové konfigurace:

```bash
python3 scripts/mailbox_switch_wizard.py
```

## Testovací skripty

Testovací skripty patří do `tests/<modul>/<projekt>/`, ne sem.
