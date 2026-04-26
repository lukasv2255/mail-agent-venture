"""
Interactive final-launch wizard for a concrete client instance.

Run from the root of a copied instance while sitting with the client:
  python3 scripts/client_instance_wizard.py

The wizard writes:
  .env              local/runtime configuration
  .env.railway      Railway variables export (ignored by git)
  NEXT_STEPS.md     non-secret checklist for the launch
"""
from __future__ import annotations

import getpass
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = PROJECT_ROOT / ".env"
RAILWAY_ENV_FILE = PROJECT_ROOT / ".env.railway"
NEXT_STEPS_FILE = PROJECT_ROOT / "NEXT_STEPS.md"


YES = {"ano", "a", "yes", "y", "true", "1"}
NO = {"ne", "n", "no", "false", "0"}


def sanitize_name(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "client"


def ask(label: str, default: str = "", required: bool = False) -> str:
    while True:
        suffix = f" [{default}]" if default else ""
        value = input(f"{label}{suffix}: ").strip()
        if not value and default:
            value = default
        if value or not required:
            return value
        print("  Hodnota je povinná.")


def ask_secret(label: str, required: bool = False) -> str:
    while True:
        value = getpass.getpass(f"{label}: ").strip()
        if value or not required:
            return value
        print("  Hodnota je povinná.")


def ask_bool(label: str, default: bool) -> bool:
    default_text = "ano" if default else "ne"
    while True:
        value = ask(f"{label} (ano/ne)", default_text).lower()
        if value in YES:
            return True
        if value in NO:
            return False
        print("  Odpověz ano nebo ne.")


def ask_choice(label: str, choices: list[str], default: str) -> str:
    choices_text = "/".join(choices)
    while True:
        value = ask(f"{label} ({choices_text})", default).lower()
        if value in choices:
            return value
        print(f"  Vyber jednu z hodnot: {choices_text}")


def ask_int(label: str, default: int, minimum: int | None = None, maximum: int | None = None) -> str:
    while True:
        raw = ask(label, str(default))
        if "#" in raw:
            print("  Bez inline komentářů. Zadej jen číslo, například 18.")
            continue
        try:
            value = int(raw)
        except ValueError:
            print("  Zadej celé číslo.")
            continue
        if minimum is not None and value < minimum:
            print(f"  Minimum je {minimum}.")
            continue
        if maximum is not None and value > maximum:
            print(f"  Maximum je {maximum}.")
            continue
        return str(value)


def as_bool(value: bool) -> str:
    return "true" if value else "false"


def env_lines(values: dict[str, str]) -> list[str]:
    return [
        "# Instance identity",
        f"CLIENT_NAME={values['client_name']}",
        "",
        "# Paths are relative to PROJECT_ROOT unless absolute.",
        "LOG_DIR=logs",
        "DATA_DIR=data",
        "PROMPTS_DIR=prompts",
        "TEMPLATES_DIR=templates",
        "",
        "# Telegram",
        f"TELEGRAM_BOT_TOKEN={values['telegram_token']}",
        f"TELEGRAM_CHAT_ID={values['telegram_chat_id']}",
        "",
        "# OpenAI",
        f"OPENAI_API_KEY={values['openai_key']}",
        "",
        "# Agent runtime",
        f"MAIL_CLIENT={values['mail_client']}",
        "KB_SOURCE=file",
        f"DRY_RUN={values['dry_run']}",
        f"AUTO_RESPOND={values['auto_respond']}",
        f"CHECK_INTERVAL_MINUTES={values['check_interval']}",
        f"DASHBOARD_PORT={values['dashboard_port']}",
        f"DASHBOARD_TOKEN={values['dashboard_token']}",
        "",
        "# Modules",
        f"MODULE_RESPONDER={values['module_responder']}",
        f"MODULE_SORTER={values['module_sorter']}",
        f"MODULE_NEWSLETTER={values['module_newsletter']}",
        "",
        "# Gmail (MAIL_CLIENT=gmail)",
        f"GMAIL_ADDRESS={values['gmail_address']}",
        "GMAIL_CREDENTIALS_FILE=credentials.json",
        "GMAIL_TOKEN_FILE=token.json",
        "# GMAIL_TOKEN_JSON=",
        "",
        "# IMAP/SMTP (MAIL_CLIENT=imap)",
        f"IMAP_HOST={values['imap_host']}",
        f"IMAP_PORT={values['imap_port']}",
        f"IMAP_USER={values['imap_user']}",
        f"IMAP_PASSWORD={values['imap_password']}",
        f"SMTP_HOST={values['smtp_host']}",
        f"SMTP_PORT={values['smtp_port']}",
        f"IMAP_INBOX_FOLDERS={values['imap_inbox_folders']}",
        f"IMAP_PROCESSED_FOLDER={values['imap_processed_folder']}",
        "",
        "# Sorter",
        f"SORTER_TARGET_FOLDER={values['sorter_target_folder']}",
        f"SORTER_POLL_INTERVAL={values['sorter_poll_interval']}",
        f"SORTER_MANUAL_LIMIT={values['sorter_manual_limit']}",
        "",
        "# Responder folders",
        f"RESPONDER_UNKNOWN={values['responder_unknown']}",
        f"RESPONDER_ESCALATED={values['responder_escalated']}",
        "",
        "# Newsletter",
        f"NEWSLETTER_HOUR={values['newsletter_hour']}",
        f"NEWSLETTER_MINUTE={values['newsletter_minute']}",
        f"NEWSLETTER_DAY={values['newsletter_day']}",
        f"NEWSLETTER_INTERVAL_DAYS={values['newsletter_interval_days']}",
        "",
        "# Microsoft Graph (MAIL_CLIENT=graph)",
        f"GRAPH_CLIENT_ID={values['graph_client_id']}",
        f"GRAPH_CLIENT_SECRET={values['graph_client_secret']}",
        f"GRAPH_TENANT_ID={values['graph_tenant_id']}",
        f"GRAPH_USER_EMAIL={values['graph_user_email']}",
        "",
        "# Helpdesk (MAIL_CLIENT=helpdesk)",
        f"HELPDESK_PROVIDER={values['helpdesk_provider']}",
        f"HELPDESK_SUBDOMAIN={values['helpdesk_subdomain']}",
        f"HELPDESK_EMAIL={values['helpdesk_email']}",
        f"HELPDESK_API_TOKEN={values['helpdesk_api_token']}",
        "",
        "# Optional database-backed KB",
        f"DATABASE_URL={values['database_url']}",
        "",
        "# launchd install overrides",
        f"LAUNCHD_LABEL={values['launchd_label']}",
        f"PYTHON_BIN={values['python_bin']}",
        "",
    ]


def write_key_value_file(path: Path, values: dict[str, str]) -> None:
    path.write_text("\n".join(env_lines(values)), encoding="utf-8")


def write_next_steps(values: dict[str, str], target: str, profile: str) -> None:
    lines = [
        "# Client Launch Checklist",
        "",
        f"- Client: `{values['client_name']}`",
        f"- Project root: `{PROJECT_ROOT}`",
        f"- Target: `{target}`",
        f"- Start profile: `{profile}`",
        f"- Mail client: `{values['mail_client']}`",
        "",
        "## Before Start",
        "",
        "- Confirm the mailbox owner approved automated sorting/reading.",
        "- Confirm target folders exist or can be created by the mail provider.",
        "- Confirm `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, and `OPENAI_API_KEY` are set.",
        "- Review client-specific prompts in `prompts/`.",
        "- Run `rg \"/Users/lukas|mail-agent-venture|C:\\\\\\\\Users\" .` and resolve real hardcoded paths.",
        "",
        "## Safe First Run",
        "",
        "- Recommended first production day: sorter on, responder off.",
        "- Watch dashboard `/api/status` and sorter history.",
        "- Use Telegram `/sort` only after confirming folders and rules.",
        "",
    ]

    if target in ("railway", "both"):
        lines += [
            "## Railway",
            "",
            "1. Link the directory to the correct Railway project/service:",
            "   `railway status`",
            "2. Import variables from `.env.railway` in Railway dashboard or CLI.",
            "3. **Add a Volume** for persistent data (rules, state):",
            "   Railway dashboard → service → Volumes → Add Volume → Mount Path: `/data`",
            "   Then set env var: `railway variables set DATA_DIR=/data`",
            "4. Deploy current code:",
            "   `railway up --detach --message \"Client launch\"`",
            "5. Verify:",
            "   `railway deployment list`",
            "   `railway logs --lines 120`",
            "6. Open the public dashboard URL and check `/api/status`.",
            "",
        ]

    if target in ("launchd", "both"):
        lines += [
            "## macOS launchd",
            "",
            "1. Install launchd plist:",
            "   `python3 scripts/install_launchd.py`",
            "2. Verify:",
            "   `launchctl print gui/$(id -u)/" + values["launchd_label"] + "`",
            "3. Watch logs:",
            "   `tail -f logs/agent.log logs/agent_err.log`",
            "",
        ]

    if values["mail_client"] == "gmail":
        lines += [
            "## Gmail OAuth",
            "",
            "- Place `credentials.json` in the project root.",
            "- Run OAuth locally: `python3 src/gmail_client.py`.",
            "- For Railway, provide `GMAIL_TOKEN_JSON` securely as an env variable.",
            "",
        ]

    NEXT_STEPS_FILE.write_text("\n".join(lines), encoding="utf-8")


def collect_values() -> tuple[dict[str, str], str, str]:
    default_name = PROJECT_ROOT.name.replace("mail-agent-", "") or "client"
    client_name = sanitize_name(ask("Název klienta/projektu", default_name, required=True))

    target = ask_choice("Kde instance poběží", ["railway", "launchd", "both"], "railway")
    profile = ask_choice("Startovací režim", ["demo", "pilot", "production"], "pilot")

    if profile == "demo":
        dry_run = True
        auto_respond = False
        module_responder_default = False
        module_sorter_default = True
        module_newsletter_default = False
    elif profile == "pilot":
        dry_run = False
        auto_respond = False
        module_responder_default = False
        module_sorter_default = True
        module_newsletter_default = False
    else:
        dry_run = False
        auto_respond = ask_bool("AUTO_RESPOND povolit automatické odpovědi", False)
        module_responder_default = ask_bool("Zapnout responder", False)
        module_sorter_default = True
        module_newsletter_default = ask_bool("Zapnout newsletter", False)

    values = {
        "client_name": client_name,
        "launchd_label": ask("Launchd label", f"com.mailagent.{client_name}"),
        "python_bin": "",
        "dashboard_port": ask_int("Dashboard port pro lokální běh", 8081, 1, 65535),
        "dashboard_token": ask_secret("Dashboard token (volitelné, Enter = bez tokenu)"),
        "telegram_token": ask_secret("Telegram bot token", required=True),
        "telegram_chat_id": ask("Telegram chat ID", required=True),
        "openai_key": ask_secret("OpenAI API key", required=True),
        "mail_client": ask_choice("Mail klient", ["imap", "gmail", "graph", "helpdesk"], "imap"),
        "dry_run": as_bool(dry_run),
        "auto_respond": as_bool(auto_respond),
        "check_interval": ask_int("CHECK_INTERVAL_MINUTES", 60, 1, 1440),
        "module_responder": as_bool(module_responder_default),
        "module_sorter": as_bool(ask_bool("Zapnout sorter", module_sorter_default)),
        "module_newsletter": as_bool(module_newsletter_default),
        "gmail_address": "",
        "imap_host": "",
        "imap_port": "993",
        "imap_user": "",
        "imap_password": "",
        "smtp_host": "",
        "smtp_port": "587",
        "imap_inbox_folders": "INBOX",
        "imap_processed_folder": "agent-processed",
        "sorter_target_folder": ask("Sorter target folder", "others", required=True),
        "sorter_poll_interval": ask_int("SORTER_POLL_INTERVAL seconds", 60, 5, 3600),
        "sorter_manual_limit": ask_int("SORTER_MANUAL_LIMIT", 200, 1, 5000),
        "responder_unknown": "agent-unknown",
        "responder_escalated": "agent-escalated",
        "newsletter_hour": "7",
        "newsletter_minute": "0",
        "newsletter_day": "0",
        "newsletter_interval_days": "7",
        "graph_client_id": "",
        "graph_client_secret": "",
        "graph_tenant_id": "",
        "graph_user_email": "",
        "helpdesk_provider": "zendesk",
        "helpdesk_subdomain": "",
        "helpdesk_email": "",
        "helpdesk_api_token": "",
        "database_url": "",
    }

    if values["mail_client"] == "imap":
        values["imap_host"] = ask("IMAP host", required=True)
        values["imap_port"] = ask_int("IMAP port", 993, 1, 65535)
        values["imap_user"] = ask("IMAP user/email", required=True)
        values["imap_password"] = ask_secret("IMAP password/app password", required=True)
        values["smtp_host"] = ask("SMTP host", required=True)
        values["smtp_port"] = ask_int("SMTP port", 587, 1, 65535)
        values["imap_inbox_folders"] = ask("IMAP inbox folders", "INBOX", required=True)
        values["imap_processed_folder"] = ask("IMAP processed folder", "agent-processed", required=True)
    elif values["mail_client"] == "gmail":
        values["gmail_address"] = ask("Gmail adresa agenta", required=True)
    elif values["mail_client"] == "graph":
        values["graph_client_id"] = ask("GRAPH_CLIENT_ID", required=True)
        values["graph_client_secret"] = ask_secret("GRAPH_CLIENT_SECRET", required=True)
        values["graph_tenant_id"] = ask("GRAPH_TENANT_ID", required=True)
        values["graph_user_email"] = ask("GRAPH_USER_EMAIL", required=True)
    elif values["mail_client"] == "helpdesk":
        values["helpdesk_provider"] = ask("Helpdesk provider", "zendesk", required=True)
        values["helpdesk_subdomain"] = ask("Helpdesk subdomain", required=True)
        values["helpdesk_email"] = ask("Helpdesk email", required=True)
        values["helpdesk_api_token"] = ask_secret("Helpdesk API token", required=True)

    if ask_bool("Zapnout newsletter", values["module_newsletter"] == "true"):
        values["module_newsletter"] = "true"
        values["newsletter_hour"] = ask_int("NEWSLETTER_HOUR", 7, 0, 23)
        values["newsletter_minute"] = ask_int("NEWSLETTER_MINUTE", 0, 0, 59)
        values["newsletter_interval_days"] = ask_int("NEWSLETTER_INTERVAL_DAYS (1=denně, 7=týdně)", 7, 1, 365)
        values["newsletter_day"] = ask_int("NEWSLETTER_DAY (0=pondělí, 6=neděle)", 0, 0, 6)
    else:
        values["module_newsletter"] = "false"

    return values, target, profile


def confirm_overwrite(path: Path) -> bool:
    if not path.exists():
        return True
    return ask_bool(f"{path.name} už existuje. Přepsat?", False)


def main() -> None:
    print("Mail Agent client launch wizard")
    print("=" * 33)
    print(f"Project root: {PROJECT_ROOT}")
    print()
    print("Průvodce zapisuje lokální tajné hodnoty do .env a .env.railway.")
    print("Tyto soubory jsou ignorované gitem. Tajné hodnoty nepiš do dokumentace.")
    print()

    if not confirm_overwrite(ENV_FILE):
        print("Zrušeno, .env zůstává beze změny.")
        return
    if not confirm_overwrite(RAILWAY_ENV_FILE):
        print("Zrušeno, .env.railway zůstává beze změny.")
        return

    values, target, profile = collect_values()
    write_key_value_file(ENV_FILE, values)
    write_key_value_file(RAILWAY_ENV_FILE, values)
    write_next_steps(values, target, profile)

    print()
    print("Hotovo.")
    print(f"- .env: {ENV_FILE}")
    print(f"- Railway env export: {RAILWAY_ENV_FILE}")
    print(f"- Checklist: {NEXT_STEPS_FILE}")
    print()
    print("Doporučené další kroky:")
    if target in ("railway", "both"):
        print("1. Ověř Railway link: railway status")
        print("2. Nahraj env hodnoty z .env.railway do Railway.")
        print("3. Přidej Volume: Railway dashboard → Volumes → Add → Mount Path: /data")
        print("   Nastav proměnnou: railway variables set DATA_DIR=/data")
        print("4. Deploy: railway up --detach --message \"Client launch\"")
        print("5. Ověř: railway deployment list && railway logs --lines 120")
    if target in ("launchd", "both"):
        print("1. Nainstaluj launchd: python3 scripts/install_launchd.py")
        print("2. Ověř logy: tail -f logs/agent.log logs/agent_err.log")
    print("5. Otevři dashboard a ověř /api/status.")


if __name__ == "__main__":
    main()
