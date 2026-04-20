"""
Odešle 2 testovací emaily z newagent7878@gmail.com na johnybb11@seznam.cz.
  - 1x spam / newsletter
  - 1x obchodní nabídka (B2B)

Použití: python scripts/send_venture_test_emails.py
"""
import base64
import sys
import time
from email.message import EmailMessage
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.gmail_client import get_gmail_service

TARGET = "johnybb11@seznam.cz"

TEST_EMAILS = [
    # MOVE — nerelevantní
    {
        "subject": "Váš web potřebuje SEO — zaručujeme 1. stránku Google",
        "body": "Analyzovali jsme váš web a zjistili vážné problémy. Naše SEO služba zaručuje výsledky do 30 dní. Cena: 2 900 Kč/měsíc.\n\nSEO Expres Team\nTel: +420 800 123 456",
    },
    # KEEP — obchodní nabídka
    {
        "subject": "Poptávka: IT služby pro naši firmu",
        "body": "Dobrý den,\n\njmenuji se Petra Horáčková, jednatelka BuildTech s.r.o. Hledáme dodavatele IT služeb — správu serverů a helpdesk pro 15 zaměstnanců.\n\nMohli bychom si domluvit call příští týden?\n\nS pozdravem,\nPetra Horáčková\nTel: +420 603 456 789",
    },
    # MOVE — nerelevantní
    {
        "subject": "Získejte 10 000 nových sledujících na Instagramu za týden!",
        "body": "Nabízíme garantovaný růst followerů na sociálních sítích. Instagram, Facebook, TikTok. Výsledky do 7 dní nebo vrácení peněz.\n\nSocial Boost Agency",
    },
    # KEEP — obchodní nabídka
    {
        "subject": "Nabídka spolupráce — účetní služby pro vaši firmu",
        "body": "Dobrý den,\n\njsem Martin Novák, certifikovaný účetní s 15 lety praxe. Hledám nové klienty pro dlouhodobou spolupráci. Nabízím vedení účetnictví, daňové přiznání a mzdovou agendu za pevnou měsíční cenu.\n\nMohli bychom se pobavit o podmínkách?\n\nMartin Novák\nTel: +420 731 222 333",
    },
    # MOVE — nerelevantní
    {
        "subject": "Faktura č. 2025-0342 — splatnost 30. dubna",
        "body": "Dobrý den,\n\nv příloze zasíláme fakturu č. 2025-0342 za měsíc březen. Splatnost: 30. dubna 2025.\n\nÚčtárna XY s.r.o.",
    },
    # KEEP — poptávka
    {
        "subject": "Zájem o vaše služby — rádi bychom se sešli",
        "body": "Dobrý den,\n\nnarážím na vás přes doporučení od Tomáše Beneše. Naše firma hledá partnera pro vývoj interního CRM systému. Máme rozpočet a jasnou specifikaci.\n\nJste k dispozici na krátkou schůzku tento nebo příští týden?\n\nJakub Procházka\nCEO, Retail Solutions s.r.o.",
    },
    # MOVE — nerelevantní
    {
        "subject": "Automatická odpověď: Jsem mimo kancelář",
        "body": "Dobrý den,\n\njsem momentálně mimo kancelář do 25. dubna. Naléhavé věci řeší kolega Jan Novák: novak@firma.cz\n\nS pozdravem",
    },
    # MOVE — nerelevantní
    {
        "subject": "Newsletter: Novinky z oboru — duben 2025",
        "body": "Vážení čtenáři,\n\npřinášíme vám přehled novinek z oboru za měsíc duben. Trh s nemovitostmi roste, inflace klesá, nové regulace EU vstoupí v platnost v červenci.\n\nRedakce BusinessNews.cz",
    },
    # KEEP — obchodní nabídka
    {
        "subject": "Dodávka kancelářského nábytku — cenová nabídka",
        "body": "Dobrý den,\n\nna základě vašeho inzerátu vám zasílám cenovou nabídku na dodávku kancelářského nábytku. Nabízíme ergonomické židle, stoly a úložné systémy s montáží a zárukou 5 let.\n\nRádi vám připravíme nabídku na míru po zaslání půdorysu prostor.\n\nLucie Marková\nObchodní zástupkyně, FurnitureB2B s.r.o.",
    },
    # MOVE — nerelevantní
    {
        "subject": "Vaše objednávka #88234 byla odeslána",
        "body": "Dobrý den,\n\nvaše objednávka č. 88234 byla předána přepravci GLS. Sledovací číslo: CZ9934821100.\n\nOčekávaná doručení: 22. dubna 2025.\n\nShopify Store",
    },
]


def send_email(service, email_def):
    msg = EmailMessage()
    msg["To"] = TARGET
    msg["Subject"] = email_def["subject"]
    for key, value in email_def.get("headers", {}).items():
        msg[key] = value
    msg.set_content(email_def["body"])
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    service.users().messages().send(userId="me", body={"raw": raw}).execute()
    print(f"  ✓ {email_def['subject'][:60]}")


def main():
    print(f"Odesílám {len(TEST_EMAILS)} testovacích emailů na {TARGET}...\n")
    service = get_gmail_service()
    for i, email_def in enumerate(TEST_EMAILS):
        send_email(service, email_def)
        if i < len(TEST_EMAILS) - 1:
            time.sleep(5)
    print("\nHotovo. Spusť: python scripts/test_sorter.py")


if __name__ == "__main__":
    main()
