"""
Test: zpětné aplikování pravidla na dříve ponechané emaily.

Pošle 3 emaily od stejného odesílatele, nechá sorter projít (kept),
pak vytvoří pravidlo from_address a spustí sort znovu — emaily musí být přesunuty.

Použití:
  python3 tests/sorter/test_rule_reapply.py
"""
import base64
import os
import sys
import time
from email.message import EmailMessage
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

from src.gmail_client import get_gmail_service

TARGET = os.getenv("TEST_TARGET_EMAIL", "")
SENDER_TAG = "reapply-test"

EMAILS = [
    {
        "subject": f"[{SENDER_TAG}] Schůzka příští týden",
        "body": "Ahoj,\n\nchtěl jsem se zeptat, jestli by ti vyhovovala schůzka příští týden ve středu kolem 10:00.\n\nDej vědět.\n\nPavel",
    },
    {
        "subject": f"[{SENDER_TAG}] Dotaz ohledně projektu",
        "body": "Dobrý den,\n\nzaujal mě váš projekt a rád bych se dozvěděl více o spolupráci.\nMůžeme si zavolat tento týden?\n\nDěkuji,\nPetr Novák",
    },
    {
        "subject": f"[{SENDER_TAG}] Potvrzení objednávky",
        "body": "Dobrý den,\n\nobjednávka č. 1234 byla přijata. Zboží expedujeme do 3 pracovních dnů.\n\nDěkujeme za nákup.",
    },
]


def send_emails(service):
    print(f"Odesílám {len(EMAILS)} testovacích emailů na {TARGET}...\n")
    for email in EMAILS:
        msg = EmailMessage()
        msg["To"] = TARGET
        msg["Subject"] = email["subject"]
        msg.set_content(email["body"])
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        service.users().messages().send(userId="me", body={"raw": raw}).execute()
        print(f"  ✓ {email['subject']}")
        time.sleep(1)
    print()


def main():
    if not TARGET:
        print("Chyba: nastav TEST_TARGET_EMAIL v .env (adresa inboxu agenta, např. johnybb11@seznam.cz)")
        sys.exit(1)

    print("POZOR: Před spuštěním tohoto testu ověř, že v sorter_rules.db")
    print("neexistuje pravidlo from_address pro odesílatele tohoto účtu.")
    print("Pokud existuje, emaily půjdou rovnou do Přesunuto a test nekrokuje správně.")
    print()

    service = get_gmail_service()
    send_emails(service)

    print("Emaily odeslány. Další kroky viz test_rule_reapply.md")
    print()
    print("Shrnutí:")
    print("  1. Počkej až agent zpracuje emaily (nebo spusť /sort)")
    print("  2. Ověř v dashboardu: 3x Ponecháno od tohoto odesílatele")
    print("  3. Na jednom klikni 'Vždy od odesílatele'")
    print("  4. Spusť /sort znovu")
    print("  5. Ověř v dashboardu: všechny 3 jsou Přesunuto")


if __name__ == "__main__":
    main()
