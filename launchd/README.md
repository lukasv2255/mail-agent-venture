# launchd — auto-restart agenta (macOS)

Soubor `com.mailagent.plist` zajišťuje automatický restart mail-agenta při pádu na macOS.

## Instalace

```bash
# Zkopíruj plist do LaunchAgents
cp launchd/com.mailagent.plist ~/Library/LaunchAgents/

# Zaregistruj a spusť
launchctl load ~/Library/LaunchAgents/com.mailagent.plist
```

Spustí se automaticky po každém přihlášení uživatele.

## Správa

```bash
# Ruční start / stop
launchctl start com.mailagent.agent
launchctl stop com.mailagent.agent

# Stav
launchctl list | grep mailagent

# Odinstalace
launchctl unload ~/Library/LaunchAgents/com.mailagent.plist
```

## Logy

| Soubor               | Obsah                             |
| -------------------- | --------------------------------- |
| `logs/agent.log`     | Standardní výstup agenta (stdout) |
| `logs/agent_err.log` | Chybový výstup (stderr)           |
| `logs/uptime.jsonl`  | Start / stop události (viz níže)  |

## Detekce pádů

`main.py` loguje do `logs/uptime.jsonl` každý start a čistý stop.
Pád = v logu je `start` bez předchozího `stop`.

```jsonl
{"event": "start", "time": "2026-04-20T08:00:00Z"}
{"event": "start", "time": "2026-04-20T09:13:42Z"}   ← pád, chybí stop
{"event": "stop",  "time": "2026-04-20T18:00:00Z"}
```

`ThrottleInterval: 5` — launchd počká 5 sekund před restartem, aby se Telegram stihl uvolnit (předchází Conflict chybě).

## Produkce (Railway)

Na Railway launchd nepoužíváme — Railway má vlastní restart policy.
Nastav: Settings → Deploy → Restart Policy: **Always**.
