"""
Interactive wizard for configuring a concrete project instance from the template.

Run from the root of a copied instance:
  python3 scripts/new_instance_wizard.py
"""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = PROJECT_ROOT / ".env"


def ask(label: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    value = input(f"{label}{suffix}: ").strip()
    return value or default


def ask_bool(label: str, default: bool) -> bool:
    default_text = "ano" if default else "ne"
    value = ask(f"{label} (ano/ne)", default_text).lower()
    return value in ("ano", "a", "yes", "y", "true", "1")


def write_env(values: dict[str, str]):
    lines = [
        "# Instance",
        f"CLIENT_NAME={values['client_name']}",
        "LOG_DIR=logs",
        "DATA_DIR=data",
        "PROMPTS_DIR=prompts",
        "TEMPLATES_DIR=templates",
        f"LAUNCHD_LABEL={values['launchd_label']}",
        "PYTHON_BIN=",
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
        "DASHBOARD_TOKEN=",
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
        "IMAP_INBOX_FOLDERS=INBOX",
        "IMAP_PROCESSED_FOLDER=agent-processed",
        "",
        "# Sorter",
        f"SORTER_TARGET_FOLDER={values['sorter_target_folder']}",
        "SORTER_POLL_INTERVAL=60",
        "SORTER_MANUAL_LIMIT=200",
        "",
        "# Responder folders",
        "RESPONDER_UNKNOWN=agent-unknown",
        "RESPONDER_ESCALATED=agent-escalated",
        "",
        "# Newsletter",
        "NEWSLETTER_HOUR=7",
        "NEWSLETTER_MINUTE=0",
        "NEWSLETTER_DAY=0",
        "NEWSLETTER_INTERVAL_DAYS=7",
        "",
        "# Microsoft Graph (MAIL_CLIENT=graph)",
        "GRAPH_CLIENT_ID=",
        "GRAPH_CLIENT_SECRET=",
        "GRAPH_TENANT_ID=",
        "GRAPH_USER_EMAIL=",
        "",
        "# Helpdesk (MAIL_CLIENT=helpdesk)",
        "HELPDESK_PROVIDER=zendesk",
        "HELPDESK_SUBDOMAIN=",
        "HELPDESK_EMAIL=",
        "HELPDESK_API_TOKEN=",
        "",
        "# Optional database-backed KB",
        "DATABASE_URL=",
        "",
    ]
    ENV_FILE.write_text("\n".join(lines), encoding="utf-8")


def main():
    print("Mail Agent instance wizard")
    print("=" * 28)
    print(f"Project root: {PROJECT_ROOT}")
    print()

    if ENV_FILE.exists():
        overwrite = ask_bool(".env už existuje. Přepsat?", False)
        if not overwrite:
            print("Zrušeno, .env zůstává beze změny.")
            return

    client_name = ask("Název klienta/projektu", PROJECT_ROOT.name.replace("mail-agent-", "") or "client")
    safe_name = "".join(ch if ch.isalnum() else "-" for ch in client_name.lower()).strip("-")

    values = {
        "client_name": safe_name,
        "launchd_label": ask("Launchd label", f"com.mailagent.{safe_name}"),
        "dashboard_port": ask("Dashboard port", "8081"),
        "telegram_token": ask("Telegram bot token"),
        "telegram_chat_id": ask("Telegram chat ID"),
        "openai_key": ask("OpenAI API key"),
        "mail_client": ask("Mail klient (imap/gmail)", "imap").lower(),
        "dry_run": str(ask_bool("DRY_RUN bezpečný režim", True)).lower(),
        "auto_respond": str(ask_bool("AUTO_RESPOND", False)).lower(),
        "check_interval": ask("CHECK_INTERVAL_MINUTES", "60"),
        "module_responder": str(ask_bool("Zapnout responder", True)).lower(),
        "module_sorter": str(ask_bool("Zapnout sorter", True)).lower(),
        "module_newsletter": str(ask_bool("Zapnout newsletter", False)).lower(),
        "gmail_address": "",
        "imap_host": "",
        "imap_port": "993",
        "imap_user": "",
        "imap_password": "",
        "smtp_host": "",
        "smtp_port": "587",
        "sorter_target_folder": ask("Sorter target folder", "others"),
    }

    if values["mail_client"] == "gmail":
        values["gmail_address"] = ask("Gmail adresa agenta")
    elif values["mail_client"] == "imap":
        values["imap_host"] = ask("IMAP host")
        values["imap_port"] = ask("IMAP port", "993")
        values["imap_user"] = ask("IMAP user/email")
        values["imap_password"] = ask("IMAP password/app password")
        values["smtp_host"] = ask("SMTP host")
        values["smtp_port"] = ask("SMTP port", "587")
    else:
        print("Neznámý mail klient. .env vytvořím, ale MAIL_CLIENT později zkontroluj ručně.")

    write_env(values)

    print()
    print(f"Hotovo: {ENV_FILE}")
    print()
    print("Doplň nebo zkontroluj ručně:")
    missing = [
        ("TELEGRAM_BOT_TOKEN", values["telegram_token"]),
        ("TELEGRAM_CHAT_ID", values["telegram_chat_id"]),
        ("OPENAI_API_KEY", values["openai_key"]),
    ]
    if values["mail_client"] == "gmail":
        missing.append(("GMAIL_ADDRESS", values["gmail_address"]))
        print("- Vlož credentials.json do rootu instance a spusť Gmail OAuth flow.")
    if values["mail_client"] == "imap":
        for key in ("imap_host", "imap_user", "imap_password", "smtp_host"):
            missing.append((key.upper(), values[key]))

    for key, value in missing:
        if not value:
            print(f"- .env: doplň {key}")

    print("- Uprav klientské prompty v prompts/")
    print("- Ověř: rg \"/Users/lukas|mail-agent-venture|C:\\\\\\\\Users\" .")
    print("- Nainstaluj/spusť launchd: python3 scripts/install_launchd.py")


if __name__ == "__main__":
    main()
