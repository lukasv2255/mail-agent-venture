"""
Odešle 8 testovacích emailů na newagent7878@gmail.com.
Použití: python scripts/send_test_emails.py
"""
import base64
import sys
import time
from email.message import EmailMessage
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.gmail_client import get_gmail_service

TARGET = "newagent7878@gmail.com"

TEST_EMAILS = [
    {
        "id": "T01",
        "subject": "Dotaz na objednávku 4471",
        "body": "Dobrý den,\nchtěl bych se zeptat, kdy dorazí moje objednávka číslo 4471.\nDěkuji, Jan Novák",
    },
    {
        "id": "T02",
        "subject": "Kde je moje zásilka - obj. 2280",
        "body": "Dobrý den,\nobjednala jsem kreatin, objednávka č. 2280. Ještě jsem nedostala žádnou informaci o odeslání.\nEva Kovářová",
    },
    {
        "id": "T03",
        "subject": "Dotaz na protein",
        "body": "Dobrý den,\nzajímá mě Whey Protein Vanilka. Kolik obsahuje bílkovin na porci a je vhodný pro vegetariány?",
    },
    {
        "id": "T04",
        "subject": "Protein a diabetes",
        "body": "Dobrý den,\nmám diabetes 2. typu a rád bych začal užívat váš protein. Je to bezpečné?",
    },
    {
        "id": "T05",
        "subject": "Chci vrátit zboží",
        "body": "Dobrý den,\nobdržel jsem objednávku 4471 ale protein mi nechutná, chci ho vrátit.\nJak mám postupovat?\nJan Novák",
    },
    {
        "id": "T06",
        "subject": "Poškozený produkt - reklamace",
        "body": "Dobrý den,\nobjednávka 1102 dorazila s poškozeným obalem a část obsahu byla rozsypaná.\nToto je nepřijatelné, chci okamžitě náhradu nebo vrácení peněz.\nJana Nováková",
    },
    {
        "id": "T07",
        "subject": "Objednávka 9999",
        "body": "Dobrý den, kdy dorazí objednávka číslo 9999?",
    },
    {
        "id": "T08",
        "subject": "Spolupráce — nabídka reklamy",
        "body": "Dobrý den, nabízíme reklamní plochy na fitness portálech. Máte zájem o spolupráci?",
    },
]


def send_email(service, test):
    msg = EmailMessage()
    msg["To"] = TARGET
    msg["Subject"] = f"[{test['id']}] {test['subject']}"
    msg.set_content(test["body"])
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    service.users().messages().send(userId="me", body={"raw": raw}).execute()
    print(f"  ✓ {test['id']} — {test['subject']}")


def main():
    print(f"Odesílám 8 testovacích emailů na {TARGET}...\n")
    service = get_gmail_service()

    for test in TEST_EMAILS:
        send_email(service, test)
        time.sleep(1)  # krátká pauza aby Gmail neblokoval

    print("\nHotovo. Spusť /check v Telegramu.")


if __name__ == "__main__":
    main()
