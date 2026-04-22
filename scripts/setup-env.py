"""
Setup skript — vytvoří .env soubor pro mail-agent.

Spuštění (jednou na každém novém PC):
  python3 scripts/setup-env.py

Pokud .env už existuje, skript se zeptá jestli ho přepsat.
"""
import os
import sys


ENV_FILE = os.path.join(os.path.dirname(__file__), "..", ".env")
ENV_FILE = os.path.normpath(ENV_FILE)


def ask(prompt, default=None, secret=False):
    if default:
        display = f"{prompt} [{default}]: "
    else:
        display = f"{prompt}: "

    value = input(display).strip()
    if not value and default:
        return default
    return value


def main():
    print("=" * 40)
    print("Mail Agent — nastavení prostředí")
    print("=" * 40)

    if os.path.exists(ENV_FILE):
        answer = input(f"\n.env již existuje. Přepsat? (ano/ne) [ne]: ").strip().lower()
        if answer not in ("ano", "a", "yes", "y"):
            print("Zrušeno.")
            sys.exit(0)

    print("\n--- Telegram ---")
    telegram_token = ask("Bot Token (od BotFather)")
    telegram_chat_id = ask("Chat ID", default="479991910")

    print("\n--- OpenAI ---")
    openai_key = ask("OpenAI API Key")

    print("\n--- Gmail ---")
    gmail_address = ask("Gmail adresa agenta", default="newagent7878@gmail.com")

    print("\n--- Agent ---")
    dry_run = ask("DRY_RUN (true = jen logy, false = odesílá emaily)", default="true")
    mail_client = ask("MAIL_CLIENT (gmail/imap/graph/helpdesk)", default="gmail")
    check_interval = ask("CHECK_INTERVAL_MINUTES (jak často kontrolovat inbox)", default="60")

    env_content = f"""# Telegram
TELEGRAM_BOT_TOKEN={telegram_token}
TELEGRAM_CHAT_ID={telegram_chat_id}

# OpenAI
OPENAI_API_KEY={openai_key}

# Gmail (MAIL_CLIENT=gmail)
GMAIL_ADDRESS={gmail_address}
GMAIL_CREDENTIALS_FILE=credentials.json
GMAIL_TOKEN_FILE=token.json
# GMAIL_TOKEN_JSON=   ← base64 token pro Railway

# IMAP (MAIL_CLIENT=imap)
# IMAP_HOST=
# IMAP_PORT=993
# IMAP_USER=
# IMAP_PASSWORD=
# SMTP_HOST=
# SMTP_PORT=587

# Microsoft Graph (MAIL_CLIENT=graph)
# GRAPH_CLIENT_ID=
# GRAPH_CLIENT_SECRET=
# GRAPH_TENANT_ID=
# GRAPH_USER_EMAIL=

# Helpdesk (MAIL_CLIENT=helpdesk)
# HELPDESK_PROVIDER=zendesk
# HELPDESK_SUBDOMAIN=
# HELPDESK_EMAIL=
# HELPDESK_API_TOKEN=

# Agent
MAIL_CLIENT={mail_client}
KB_SOURCE=file
DRY_RUN={dry_run}
CHECK_INTERVAL_MINUTES={check_interval}
"""

    with open(ENV_FILE, "w", encoding="utf-8") as f:
        f.write(env_content)

    print(f"\n✅ .env vytvořen: {ENV_FILE}")
    print("\nDalší kroky:")
    print("  1. Vlož credentials.json do root projektu (Google Cloud Console)")
    print("  2. Spusť OAuth flow: python3 src/gmail_client.py")
    print("  3. Spusť agenta:     python3 main.py")


if __name__ == "__main__":
    main()
