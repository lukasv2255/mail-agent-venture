"""
Test: tělo emailu se zobrazuje na dashboardu (HTML-only emaily).

Odesílá 3 testovací emaily:
  1. HTML-only email bez plain text části  ← hlavní případ bugu
  2. Multipart email (plain text + HTML)   ← standardní případ, musí fungovat vždy
  3. Plain text email                      ← referenční případ

Použití:
  python3 tests/email_body/send_html_body_test.py

Prerekvizity:
  - .env s GMAIL_ADDRESS a TEST_TARGET_EMAIL (nebo GMAIL_ADDRESS jako fallback)
  - platný credentials.json / token.json pro Gmail API

Co ověřit po spuštění:
  1. Sorter zpracuje emaily (sleduj logy nebo dashboard → Sorter sekce)
  2. Rozklikni každý řádek v dashboardu
  3. Všechny 3 emaily musí zobrazit čitelný text, ne '—'
"""
import base64
import os
import sys
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.message import EmailMessage
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

from src.gmail_client import get_gmail_service

TARGET = os.getenv("TEST_TARGET_EMAIL", os.getenv("IMAP_USER", os.getenv("GMAIL_ADDRESS", "")))

PLAIN_BODY = (
    "Dobrý den,\n\n"
    "píši vám ohledně možné spolupráce na vývoji webové aplikace.\n"
    "Jsme startup z Brna, hledáme vývojářský tým pro React + FastAPI projekt.\n\n"
    "Mohli bychom si domluvit krátký hovor příští týden?\n\n"
    "S pozdravem,\n"
    "Jana Procházková\n"
    "CEO, AppStart s.r.o.\n"
    "Tel: +420 731 555 888"
)

HTML_BODY = """\
<html>
  <body>
    <p>Dobrý den,</p>
    <p>píši vám ohledně možné spolupráce na vývoji webové aplikace.<br>
    Jsme startup z Brna, hledáme vývojářský tým pro React + FastAPI projekt.</p>
    <p>Mohli bychom si domluvit krátký hovor příští týden?</p>
    <p>S pozdravem,<br>
    <strong>Jana Procházková</strong><br>
    CEO, AppStart s.r.o.<br>
    Tel: +420 731 555 888</p>
  </body>
</html>
"""

# HTML s inline CSS styly — typický výstup Apple Mail / Outlook
# Přesně tento formát byl zachycen v bugu (screenshot)
APPLE_MAIL_HTML_BODY = """\
<html><body>\
<div data-pasted="true">Dobrý den,</div>\
<div><br></div>\
<div>provozujeme Villa Stella v Prešove, ktorá je vhodná pre dlhodobé ubytovanie montážnych alebo projektových tímov.</div>\
<div><br></div>\
<div>Ide o 3-izbový apartmán so spálňami, kuchyňou, terasou, bazénom a parkovaním v tichom prostredí.</div>\
<div><br></div>\
<div>Riešite ubytovanie projektu v tomto regióne? Rád pošlem detaily.</div>\
<div><br></div>\
<div><em>S pozdravom / Kind regards,</em></div>\
<div><em>Ján Chovanec</em></div>\
<div><em>Antonio - Old Town Residence &amp; Villa Stella</em></div>\
<div style="box-sizing: border-box; border: 0px solid rgb(226, 232, 240); color: rgb(65, 65, 65); font-family: sans-serif; font-size: 14px;">\
<br></div>\
<div style="box-sizing: border-box; border: 0px solid rgb(226, 232, 240); color: rgb(65, 65, 65); font-family: sans-serif; font-size: 14px;">\
+421 948 759</div>\
</body></html>
"""


def _send_raw(service, msg):
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    service.users().messages().send(userId="me", body={"raw": raw}).execute()


def send_html_only(service):
    """Email bez plain text části — starý kód vracel body='' pro tento případ."""
    msg = MIMEMultipart("alternative")
    msg["To"] = TARGET
    msg["Subject"] = "[TEST body-display] HTML-only email — žádný plain text"
    msg.attach(MIMEText(HTML_BODY, "html", "utf-8"))
    _send_raw(service, msg)
    print("  ✓ HTML-only email odeslán")


def send_multipart(service):
    """Standardní multipart email (plain text + HTML) — musí fungovat vždy."""
    msg = MIMEMultipart("alternative")
    msg["To"] = TARGET
    msg["Subject"] = "[TEST body-display] Multipart email — plain text + HTML"
    msg.attach(MIMEText(PLAIN_BODY, "plain", "utf-8"))
    msg.attach(MIMEText(HTML_BODY, "html", "utf-8"))
    _send_raw(service, msg)
    print("  ✓ Multipart email odeslán")


def send_plain_text(service):
    """Čistý plain text email — referenční případ."""
    msg = EmailMessage()
    msg["To"] = TARGET
    msg["Subject"] = "[TEST body-display] Plain text email — referenční případ"
    msg.set_content(PLAIN_BODY)
    _send_raw(service, msg)
    print("  ✓ Plain text email odeslán")


def send_apple_mail_html(service):
    """HTML s inline CSS styly — typický výstup Apple Mail / Outlook.
    Přesně tento formát způsobil bug zachycený na screenshotu."""
    msg = MIMEMultipart("alternative")
    msg["To"] = TARGET
    msg["Subject"] = "[TEST body-display] Apple Mail styl — HTML s inline CSS"
    msg.attach(MIMEText(APPLE_MAIL_HTML_BODY, "html", "utf-8"))
    _send_raw(service, msg)
    print("  ✓ Apple Mail HTML email odeslán")


def main():
    if not TARGET:
        print("Chyba: nastav TEST_TARGET_EMAIL nebo GMAIL_ADDRESS v .env")
        sys.exit(1)

    print(f"Odesílám 4 testovací emaily na {TARGET}...\n")
    service = get_gmail_service()

    send_html_only(service)
    time.sleep(3)
    send_multipart(service)
    time.sleep(3)
    send_plain_text(service)
    time.sleep(3)
    send_apple_mail_html(service)

    print(
        "\nHotovo. Co ověřit:\n"
        "  1. Počkej až sorter emaily zpracuje (KEEP nebo MOVE)\n"
        "  2. Dashboard → Sorter sekce → rozklikni každý [TEST body-display] řádek\n"
        "  3. Všechny 4 musí zobrazit čitelný text, ne '—'\n"
        "  4. Apple Mail email nesmí zobrazovat raw HTML tagy ani inline CSS styly"
    )


if __name__ == "__main__":
    main()
