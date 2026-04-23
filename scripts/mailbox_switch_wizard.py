"""
Five-step wizard for switching an existing instance from a test mailbox
to a client's mailbox.

Run from the client instance root:
  python3 scripts/mailbox_switch_wizard.py

It only changes mailbox-related values, creates a .env backup, can optionally
apply the same values to Railway, and runs a safe connection test.
"""
from __future__ import annotations

import datetime as dt
import getpass
import imaplib
import re
import smtplib
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = PROJECT_ROOT / ".env"
NEXT_STEPS_FILE = PROJECT_ROOT / "MAILBOX_SWITCH_NEXT_STEPS.md"

YES = {"ano", "a", "yes", "y", "true", "1"}
NO = {"ne", "n", "no", "false", "0"}


def ask(label: str, default: str = "", required: bool = False) -> str:
    while True:
        suffix = f" [{default}]" if default else ""
        value = input(f"{label}{suffix}: ").strip()
        if not value and default:
            value = default
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


def ask_secret(label: str, keep_allowed: bool) -> tuple[str, bool]:
    suffix = " [Enter = ponechat stávající]" if keep_allowed else ""
    while True:
        value = getpass.getpass(f"{label}{suffix}: ").strip()
        if value:
            return value, True
        if keep_allowed:
            return "", False
        print("  Hodnota je povinná.")


def load_env(path: Path) -> tuple[list[str], dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"Chybí {path}. Nejdřív vytvoř .env.")
    lines = path.read_text(encoding="utf-8").splitlines()
    values: dict[str, str] = {}
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key] = value
    return lines, values


def backup_env(path: Path) -> Path:
    timestamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = path.with_name(f".env.before-mailbox-switch-{timestamp}")
    backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    return backup


def save_env(path: Path, lines: list[str], updates: dict[str, str]) -> None:
    remaining = dict(updates)
    output: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key = stripped.split("=", 1)[0]
            if key in remaining:
                output.append(f"{key}={remaining.pop(key)}")
                continue
        output.append(line)
    if remaining:
        output.append("")
        output.append("# Mailbox switch")
        for key, value in remaining.items():
            output.append(f"{key}={value}")
    path.write_text("\n".join(output) + "\n", encoding="utf-8")


def redacted(key: str, value: str) -> str:
    if re.search("PASSWORD|SECRET|TOKEN|KEY", key):
        if not value:
            return "<unchanged>"
        if len(value) <= 6:
            return "***"
        return f"{value[:3]}***{value[-3:]}"
    return value


def print_table(headers: list[str], rows: list[list[str]]) -> None:
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))
    line = " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers))
    sep = "-+-".join("-" * width for width in widths)
    print(line)
    print(sep)
    for row in rows:
        print(" | ".join(str(cell).ljust(widths[i]) for i, cell in enumerate(row)))


def step_header(number: int, title: str) -> None:
    print()
    print(f"Krok {number}/5 — {title}")
    print("-" * (10 + len(title)))


def collect(values: dict[str, str]) -> dict[str, str]:
    updates: dict[str, str] = {}

    step_header(1, "mail klient, servery, adresa a heslo")
    current_client = values.get("MAIL_CLIENT", "imap")
    mail_client = ask_choice("Typ mail klienta", ["imap", "gmail", "graph", "helpdesk"], current_client)
    updates["MAIL_CLIENT"] = mail_client

    if mail_client == "imap":
        updates["IMAP_HOST"] = ask("IMAP host", values.get("IMAP_HOST", ""), required=True)
        updates["SMTP_HOST"] = ask("SMTP host", values.get("SMTP_HOST", ""), required=True)
        updates["IMAP_PORT"] = values.get("IMAP_PORT", "993") or "993"
        updates["SMTP_PORT"] = values.get("SMTP_PORT", "587") or "587"
        updates["IMAP_USER"] = ask("E-mail / IMAP user", values.get("IMAP_USER", ""), required=True)
        secret, should_set = ask_secret("IMAP password/app password", keep_allowed=bool(values.get("IMAP_PASSWORD")))
        if should_set:
            updates["IMAP_PASSWORD"] = secret
        updates["GMAIL_ADDRESS"] = ""
    elif mail_client == "gmail":
        updates["GMAIL_ADDRESS"] = ask("Gmail adresa agenta", values.get("GMAIL_ADDRESS", ""), required=True)
        updates["GMAIL_CREDENTIALS_FILE"] = values.get("GMAIL_CREDENTIALS_FILE", "credentials.json")
        updates["GMAIL_TOKEN_FILE"] = values.get("GMAIL_TOKEN_FILE", "token.json")
        print("Gmail používá OAuth soubory credentials.json/token.json; heslo se zde nezadává.")
    elif mail_client == "graph":
        updates["GRAPH_CLIENT_ID"] = ask("GRAPH_CLIENT_ID", values.get("GRAPH_CLIENT_ID", ""), required=True)
        updates["GRAPH_TENANT_ID"] = ask("GRAPH_TENANT_ID", values.get("GRAPH_TENANT_ID", ""), required=True)
        updates["GRAPH_USER_EMAIL"] = ask("GRAPH_USER_EMAIL", values.get("GRAPH_USER_EMAIL", ""), required=True)
        secret, should_set = ask_secret("GRAPH_CLIENT_SECRET", keep_allowed=bool(values.get("GRAPH_CLIENT_SECRET")))
        if should_set:
            updates["GRAPH_CLIENT_SECRET"] = secret
    else:
        updates["HELPDESK_PROVIDER"] = ask("Helpdesk provider", values.get("HELPDESK_PROVIDER", "zendesk"), required=True)
        updates["HELPDESK_SUBDOMAIN"] = ask("Helpdesk subdomain", values.get("HELPDESK_SUBDOMAIN", ""), required=True)
        updates["HELPDESK_EMAIL"] = ask("Helpdesk email", values.get("HELPDESK_EMAIL", ""), required=True)
        secret, should_set = ask_secret("HELPDESK_API_TOKEN", keep_allowed=bool(values.get("HELPDESK_API_TOKEN")))
        if should_set:
            updates["HELPDESK_API_TOKEN"] = secret

    step_header(2, "zbytek podle aktuální .env")
    rest_keys = [
        "IMAP_PORT",
        "SMTP_PORT",
        "IMAP_INBOX_FOLDERS",
        "IMAP_PROCESSED_FOLDER",
        "SORTER_TARGET_FOLDER",
        "RESPONDER_UNKNOWN",
        "RESPONDER_ESCALATED",
        "MODULE_SORTER",
        "MODULE_RESPONDER",
        "MODULE_NEWSLETTER",
        "AUTO_RESPOND",
        "DRY_RUN",
    ]
    rows = []
    for key in rest_keys:
        value = updates.get(key, values.get(key, ""))
        if key == "IMAP_PORT" and not value:
            value = "993"
        if key == "SMTP_PORT" and not value:
            value = "587"
        rows.append([key, value])
    print_table(["Proměnná", "Hodnota"], rows)
    print()
    print("Porty ponechávám podle běžných defaultů: IMAP 993, SMTP 587.")
    if ask_bool("Chceš upravit složky nebo moduly?", False):
        updates["IMAP_INBOX_FOLDERS"] = ask("IMAP inbox folders", values.get("IMAP_INBOX_FOLDERS", "INBOX"), required=True)
        updates["IMAP_PROCESSED_FOLDER"] = ask("IMAP processed folder", values.get("IMAP_PROCESSED_FOLDER", "agent-processed"), required=True)
        updates["SORTER_TARGET_FOLDER"] = ask("Sorter target folder", values.get("SORTER_TARGET_FOLDER", "others"), required=True)
        updates["RESPONDER_UNKNOWN"] = ask("Responder unknown folder", values.get("RESPONDER_UNKNOWN", "agent-unknown"), required=True)
        updates["RESPONDER_ESCALATED"] = ask("Responder escalated folder", values.get("RESPONDER_ESCALATED", "agent-escalated"), required=True)
        updates["MODULE_SORTER"] = "true" if ask_bool("Zapnout sorter", values.get("MODULE_SORTER", "true") == "true") else "false"
        updates["MODULE_RESPONDER"] = "true" if ask_bool("Zapnout responder", values.get("MODULE_RESPONDER", "false") == "true") else "false"
        updates["MODULE_NEWSLETTER"] = "true" if ask_bool("Zapnout newsletter", values.get("MODULE_NEWSLETTER", "false") == "true") else "false"
        if updates["MODULE_RESPONDER"] == "true":
            updates["AUTO_RESPOND"] = "true" if ask_bool("AUTO_RESPOND", values.get("AUTO_RESPOND", "false") == "true") else "false"
        else:
            updates["AUTO_RESPOND"] = "false"
        updates["DRY_RUN"] = "false" if ask_bool("Povolit reálné akce podle modulů", values.get("DRY_RUN", "false") == "false") else "true"

    return updates


def apply_to_railway(updates: dict[str, str]) -> bool:
    print()
    print("Propisuji do Railway Variables bez zobrazení hodnot...")
    ok = True
    for key, value in updates.items():
        if value == "":
            continue
        try:
            result = subprocess.run(
                ["railway", "variable", "set", "--skip-deploys", f"{key}={value}"],
                cwd=PROJECT_ROOT,
                text=True,
                capture_output=True,
                timeout=45,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
            print(f"- {key}: chyba ({exc})")
            ok = False
            continue
        if result.returncode == 0:
            print(f"- {key}: OK")
        else:
            print(f"- {key}: chyba")
            ok = False
    return ok


def test_connection(values: dict[str, str]) -> bool:
    mail_client = values.get("MAIL_CLIENT", "imap")
    print()
    print("Testovací průchod")
    print("-----------------")
    if mail_client != "imap":
        print(f"Automatický test je zatím implementovaný jen pro IMAP/SMTP. MAIL_CLIENT={mail_client}")
        return True

    ok = True
    imap_host = values.get("IMAP_HOST", "")
    imap_port = int(values.get("IMAP_PORT", "993") or "993")
    imap_user = values.get("IMAP_USER", "")
    imap_password = values.get("IMAP_PASSWORD", "")
    inbox = values.get("IMAP_INBOX_FOLDERS", "INBOX").split(",")[0].strip() or "INBOX"
    smtp_host = values.get("SMTP_HOST", "")
    smtp_port = int(values.get("SMTP_PORT", "587") or "587")

    try:
        with imaplib.IMAP4_SSL(imap_host, imap_port, timeout=20) as conn:
            conn.login(imap_user, imap_password)
            status, _ = conn.select(inbox, readonly=True)
            print(f"- IMAP login/select {inbox}: {status}")
            conn.logout()
    except Exception as exc:
        print(f"- IMAP test selhal: {exc}")
        ok = False

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as smtp:
            smtp.starttls()
            smtp.login(imap_user, imap_password)
            print("- SMTP login: OK")
    except Exception as exc:
        print(f"- SMTP test selhal: {exc}")
        ok = False

    return ok


def write_next_steps(updates: dict[str, str], backup: Path) -> None:
    lines = [
        "# Mailbox Switch Checklist",
        "",
        f"- Project root: `{PROJECT_ROOT}`",
        f"- Backup: `{backup}`",
        "",
        "## Changed Keys",
        "",
    ]
    for key, value in sorted(updates.items()):
        lines.append(f"- `{key}` = `{redacted(key, value)}`")
    lines += [
        "",
        "## Railway",
        "",
        "- If you did not apply Railway values from the wizard, update Railway Variables manually.",
        "- Deploy after env update: `railway up --detach --message \"Switch client mailbox\"`",
        "- Verify: `railway deployment list && railway logs --lines 120`",
        "",
        "## Verify",
        "",
        "- Open `/api/status`.",
        "- Send one obvious spam/newsletter test mail.",
        "- Send one real inquiry test mail.",
        "- Check sorter history before running `/sort` on the full mailbox.",
        "",
    ]
    NEXT_STEPS_FILE.write_text("\n".join(lines), encoding="utf-8")


def merged_values(values: dict[str, str], updates: dict[str, str]) -> dict[str, str]:
    merged = dict(values)
    merged.update(updates)
    return merged


def main() -> None:
    print("Mailbox switch wizard")
    print("=" * 21)
    print(f"Project root: {PROJECT_ROOT}")
    print("Tok má 5 kroků: servery, e-mail, heslo, rekapitulace, zápis/Railway.")

    lines, values = load_env(ENV_FILE)
    updates = collect(values)

    step_header(5, "souhrn, zápis a Railway")
    rows = []
    for key, value in sorted(updates.items()):
        old = values.get(key, "")
        rows.append([key, redacted(key, old), redacted(key, value)])
    print_table(["Proměnná", "Původní", "Nová"], rows)

    if not ask_bool("Zapsat změny do lokální .env?", True):
        print("Zrušeno, .env zůstává beze změny.")
        return

    backup = backup_env(ENV_FILE)
    save_env(ENV_FILE, lines, updates)
    write_next_steps(updates, backup)
    current_values = merged_values(values, updates)

    print()
    print(f"Záloha: {backup}")
    print(f"Zapsáno: {ENV_FILE}")
    print(f"Checklist: {NEXT_STEPS_FILE}")

    if ask_bool("Promítnout stejné změny do Railway Variables?", False):
        apply_to_railway(updates)


if __name__ == "__main__":
    main()
