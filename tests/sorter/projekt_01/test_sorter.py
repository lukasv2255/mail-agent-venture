"""
Odešle 30 testovacích emailů na TEST_TARGET_EMAIL.
  - 12x spam (MOVE)
  -  8x poptávka služby (KEEP)
  - 10x e-shop newsletter / propagační email (MOVE)

Použití: python tests/sorter/projekt_01/test_sorter.py
"""
import base64
import os
import sys
import time
from email.message import EmailMessage
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.gmail_client import get_gmail_service

TARGET = os.getenv("TEST_TARGET_EMAIL", os.getenv("GMAIL_ADDRESS", ""))

TEST_EMAILS = [
    # ── SPAM (MOVE) ────────────────────────────────────────────────────────────

    # S01
    {
        "subject": "Váš web potřebuje SEO — zaručujeme 1. stránku Google",
        "body": (
            "Analyzovali jsme váš web a zjistili vážné problémy.\n"
            "Naše SEO služba zaručuje výsledky do 30 dní. Cena: 2 900 Kč/měsíc.\n\n"
            "SEO Expres Team\nTel: +420 800 123 456\n\n"
            "Odhlásit se z odběru: klikněte zde"
        ),
    },
    # S02
    {
        "subject": "Získejte 10 000 nových sledujících na Instagramu za týden!",
        "body": (
            "Nabízíme garantovaný růst followerů na sociálních sítích.\n"
            "Instagram, Facebook, TikTok. Výsledky do 7 dní nebo vrácení peněz.\n\n"
            "Social Boost Agency\nwww.socialboost.cz"
        ),
    },
    # S03
    {
        "subject": "Vydělávejte z domova 50 000 Kč měsíčně — bez zkušeností!",
        "body": (
            "Stovky lidí již vydělávají z domova díky našemu systému.\n"
            "Žádné investice, žádné zkušenosti. Stačí počítač a internet.\n"
            "Registrujte se zdarma: www.vydelajdoma.cz\n\n"
            "Tato zpráva byla zaslána na základě vaší registrace."
        ),
    },
    # S04
    {
        "subject": "URGENTNÍ: Váš bankovní účet byl dočasně omezen",
        "body": (
            "Vážený kliente,\n\n"
            "z bezpečnostních důvodů byl váš účet dočasně omezen.\n"
            "Pro obnovení přístupu klikněte na odkaz níže a ověřte svou totožnost.\n\n"
            ">> Ověřit účet <<\n\n"
            "Bezpečnostní tým Vaší Banky"
        ),
    },
    # S05
    {
        "subject": "Investujte do kryptoměn — zaručený výnos 300 % ročně",
        "body": (
            "Náš algoritmus generuje stabilní výnosy bez ohledu na trh.\n"
            "Minimální vklad: 500 EUR. Výnosy vypláceny každý měsíc.\n"
            "Omezená kapacita — zaregistrujte se ještě dnes.\n\n"
            "CryptoProfit s.r.o."
        ),
    },
    # S06
    {
        "subject": "Pronájem databáze 50 000 ověřených B2B kontaktů",
        "body": (
            "Oslovte svou cílovou skupinu přesně a efektivně.\n"
            "Nabízíme pronájem segmentovaných B2B kontaktů dle oboru, velikosti firmy a regionu.\n"
            "Cena od 1,50 Kč/kontakt. Ukázka zdarma na vyžádání.\n\n"
            "DataLead s.r.o. | obchod@datalead.cz"
        ),
    },
    # S07
    {
        "subject": "Máte nevyzvednutý balíček — potvrďte doručení",
        "body": (
            "Vážený zákazníku,\n\n"
            "pokoušeli jsme se vám doručit zásilku, ale nikdo nebyl doma.\n"
            "Pro nové doručení zaplaťte poplatek 49 Kč a vyberte termín.\n\n"
            ">> Potvrdit doručení <<\n\n"
            "Doručovací služba CZ"
        ),
    },
    # S08
    {
        "subject": "Bezplatný audit vašeho webu — pouze dnes!",
        "body": (
            "Získejte ZDARMA kompletní SEO a UX audit vašeho webu v hodnotě 4 900 Kč.\n"
            "Nabídka platí pouze dnes. Stačí zadat URL svého webu.\n\n"
            ">> Spustit bezplatný audit <<\n\n"
            "WebAudit Pro | info@webauditpro.cz"
        ),
    },
    # S09
    {
        "subject": "Hromadné SMS a e-maily — získejte zákazníky levně",
        "body": (
            "Rozesílejte hromadné SMS a emaily přímo z našeho systému.\n"
            "Ceny od 0,09 Kč/SMS. Bez smluv, bez závazků.\n"
            "Vyzkoušejte zdarma — 500 SMS jako bonus při registraci.\n\n"
            "BulkSend.cz | podpora@bulksend.cz"
        ),
    },
    # S10
    {
        "subject": "Zhubnete 10 kg za 30 dní — klinicky ověřeno",
        "body": (
            "Revoluční přípravek spalující tuk 3× rychleji než dieta.\n"
            "Bez jo-jo efektu. Klinická studie na 1 200 pacientech.\n"
            "Objednejte nyní se slevou 40 %: www.slimfast.cz\n\n"
            "SlimFast Nutrition | Odhlásit odběr"
        ),
    },
    # S11
    {
        "subject": "Vaše firma může získat dotaci až 2 000 000 Kč — zjistěte jak",
        "body": (
            "Dotační program EU 2025 — firmy mohou žádat o nevratné dotace.\n"
            "Specializujeme se na přípravu žádostí. Úspěšnost 94 %.\n"
            "Konzultace zdarma: volejte 800 222 333.\n\n"
            "EUDotace.cz — zasíláme všem podnikatelům v databázi"
        ),
    },
    # S12
    {
        "subject": "Automatická odpověď: Jsem mimo kancelář do 28. dubna",
        "body": (
            "Dobrý den,\n\n"
            "jsem momentálně mimo kancelář a vrátím se 28. dubna.\n"
            "Naléhavé věci prosím řešte s kolegou Janem Novákem: novak@firma.cz\n\n"
            "S pozdravem"
        ),
    },

    # ── POPTÁVKY SLUŽBY (KEEP) ─────────────────────────────────────────────────

    # P01
    {
        "subject": "Poptávka: IT služby pro naši firmu",
        "body": (
            "Dobrý den,\n\n"
            "jmenuji se Petra Horáčková, jednatelka BuildTech s.r.o.\n"
            "Hledáme dodavatele IT služeb — správu serverů a helpdesk pro 15 zaměstnanců.\n\n"
            "Mohli bychom si domluvit call příští týden?\n\n"
            "S pozdravem,\nPetra Horáčková\nTel: +420 603 456 789"
        ),
    },
    # P02
    {
        "subject": "Nabídka spolupráce — účetní a daňové služby pro vaši firmu",
        "body": (
            "Dobrý den,\n\n"
            "jsem Martin Novák, certifikovaný účetní s 15 lety praxe.\n"
            "Hledám nové klienty pro dlouhodobou spolupráci.\n"
            "Nabízím vedení účetnictví, daňové přiznání a mzdovou agendu za pevnou měsíční cenu.\n\n"
            "Mohli bychom se pobavit o podmínkách?\n\n"
            "Martin Novák\nTel: +420 731 222 333"
        ),
    },
    # P03
    {
        "subject": "Zájem o vaše služby — rádi bychom se sešli",
        "body": (
            "Dobrý den,\n\n"
            "narážím na vás přes doporučení od Tomáše Beneše.\n"
            "Naše firma hledá partnera pro vývoj interního CRM systému.\n"
            "Máme rozpočet a jasnou specifikaci.\n\n"
            "Jste k dispozici na krátkou schůzku tento nebo příští týden?\n\n"
            "Jakub Procházka\nCEO, Retail Solutions s.r.o."
        ),
    },
    # P04
    {
        "subject": "Dodávka kancelářského nábytku — cenová nabídka",
        "body": (
            "Dobrý den,\n\n"
            "na základě vašeho inzerátu vám zasílám cenovou nabídku na dodávku kancelářského nábytku.\n"
            "Nabízíme ergonomické židle, stoly a úložné systémy s montáží a zárukou 5 let.\n\n"
            "Rádi vám připravíme nabídku na míru po zaslání půdorysu prostor.\n\n"
            "Lucie Marková\nObchodní zástupkyně, FurnitureB2B s.r.o."
        ),
    },
    # P05
    {
        "subject": "Poptávka: vývoj e-shopu pro náš doplňkový sortiment",
        "body": (
            "Dobrý den,\n\n"
            "provozujeme malý e-shop s doplňky stravy a plánujeme přechod na novou platformu.\n"
            "Hledáme vývojáře, který by nám připravil nový web na míru — WooCommerce nebo Shoptet.\n\n"
            "Máte s takovými projekty zkušenosti? Mohli bychom probrat rozsah a cenu?\n\n"
            "Ondřej Šimánek\njednatel, VitaShop.cz\nTel: +420 777 100 200"
        ),
    },
    # P06
    {
        "subject": "Zájem o marketingové služby — startup v oblasti healthtech",
        "body": (
            "Dobrý den,\n\n"
            "jsem spoluzakladatel healthtech startupu. Chystáme se na trh a hledáme\n"
            "marketingovou agenturu nebo freelancera pro launch kampaň.\n\n"
            "Zajímalo by mě, jestli máte zkušenosti s B2C kampněmi v oblasti zdraví a výživy.\n\n"
            "Radek Vávra\nCo-founder, HealthMate s.r.o."
        ),
    },
    # P07
    {
        "subject": "Hledáme dodavatele pro rekonstrukci a vybavení nových kanceláří",
        "body": (
            "Dobrý den,\n\n"
            "naše firma expanduje a otevíráme nové kancelářské prostory v Brně (300 m²).\n"
            "Potřebujeme dodavatele pro kompletní vybavení — nábytek, osvětlení, IT infrastruktura.\n\n"
            "Byl bych rád, kdybychom se mohli sejít a probrali vaše portfolio a orientační ceny.\n\n"
            "Ing. Filip Kratochvíl\nOperační ředitel, LogiCorp a.s.\nTel: +420 602 888 777"
        ),
    },
    # P08
    {
        "subject": "Spolupráce na vývoji mobilní aplikace — máme specifikaci",
        "body": (
            "Dobrý den,\n\n"
            "narazil jsem na vaše portfolio a líbí se mi vaše práce.\n"
            "Chceme vyvinout mobilní aplikaci (iOS + Android) pro správu firemních objednávek.\n"
            "Máme připravenou specifikaci a wireframy, hledáme vývojářský tým.\n\n"
            "Mohli bychom domluvit úvodní hovor tento týden?\n\n"
            "Tomáš Beneš\nProduct Owner, OrderFlow s.r.o."
        ),
    },

    # ── E-SHOP NEWSLETTERY (MOVE) ──────────────────────────────────────────────

    # N01
    {
        "subject": "Alza.cz: Velký jarní výprodej — slevy až 60 %",
        "body": (
            "Ahoj,\n\n"
            "jarní výprodej právě začal! Vybrali jsme pro tebe stovky produktů se slevou až 60 %.\n\n"
            "🔥 Notebooky od 9 990 Kč\n"
            "🔥 Sluchátka od 299 Kč\n"
            "🔥 Herní periferie -30 %\n\n"
            "Nakupuj na alza.cz\n\n"
            "Tento email dostáváš, protože jsi přihlášen k odběru novinek Alza.cz.\n"
            "Odhlásit se | Alza.cz a.s., Jankovcova 1522/53, Praha 7"
        ),
    },
    # N02
    {
        "subject": "Mall.cz: Nové produkty a akční nabídky tohoto týdne",
        "body": (
            "Dobré ráno,\n\n"
            "přinášíme ti přehled nejlepších nabídek tohoto týdne na Mall.cz.\n\n"
            "Spotřebiče do domácnosti — sleva 20 %\n"
            "Nová kolekce zahradního nábytku — od 1 290 Kč\n"
            "Dětské hračky — výprodej skladových zásob\n\n"
            "Prozkoumat nabídky → mall.cz\n\n"
            "Mall International a.s. | Odhlásit odběr newsletteru"
        ),
    },
    # N03
    {
        "subject": "Sportisimo: Nová kolekce jaro 2025 + sleva 15 % pro tebe",
        "body": (
            "Ahoj,\n\n"
            "nová jarní kolekce dorazila do Sportisimo!\n"
            "Jako věrný zákazník máš exkluzivní slevu 15 % na celý nový sortiment.\n\n"
            "Kód: JARO15\n"
            "Platnost: do 30. dubna 2025\n\n"
            "Prohlédnout kolekci → sportisimo.cz\n\n"
            "Sportisimo s.r.o. | Jsi na tomto seznamu, protože jsi u nás nakoupil.\n"
            "Odhlásit odběr"
        ),
    },
    # N04
    {
        "subject": "CZC.cz: Grafické karty a herní PC nyní za nejlepší ceny",
        "body": (
            "Čau,\n\n"
            "právě jsme naskladnili nové grafické karty RTX 5000 series.\n"
            "Ceny začínají na 12 990 Kč. Navíc herní PC sestavy s dopravou zdarma.\n\n"
            ">> Zobrazit herní počítače na CZC.cz <<\n\n"
            "CZC.cz s.r.o. | Odesíláme protože jsi registrovaný zákazník.\n"
            "Odhlásit se od newsletteru"
        ),
    },
    # N05
    {
        "subject": "Notino.cz: Váš oblíbený parfém je znovu skladem",
        "body": (
            "Dobrá zpráva!\n\n"
            "Produkt, který jsi si uložil do wishlistu, je opět dostupný:\n\n"
            "Chanel Bleu de Chanel EDP 100 ml — 3 490 Kč\n\n"
            "Naskladnění bývá rychle vyprodáno. Objednáš?\n\n"
            ">> Přejít k produktu <<\n\n"
            "Notino s.r.o. | Tuto notifikaci jsi zapnul ve svém účtu. Vypnout upozornění."
        ),
    },
    # N06
    {
        "subject": "Rohlík.cz: Speciální nabídky na tento víkend 🛒",
        "body": (
            "Ahoj,\n\n"
            "připravili jsme pro tebe výběr víkendových akčních nabídek:\n\n"
            "🥩 Hovězí svíčková -25 %\n"
            "🍷 Výběrová vína od 99 Kč\n"
            "🧴 Drogerie — druhý produkt za 1 Kč\n\n"
            "Doručíme dnes večer nebo zítra dopoledne.\n\n"
            "Rohlik.cz | Zasíláme jako součást věrnostního programu.\n"
            "Změnit frekvenci emailů | Odhlásit odběr"
        ),
    },
    # N07
    {
        "subject": "Zara: Exkluzivní přístup k nové kolekci — pouze pro členy",
        "body": (
            "Ahoj,\n\n"
            "jako člen Zara-club máš jako první přístup k naší nové kolekci jaro/léto 2025.\n"
            "Kolekce je dostupná od dnes, 8:00. Doporučujeme neváhat — klíčové kusy mizí rychle.\n\n"
            "Prohlédnout kolekci → zara.com\n\n"
            "Inditex s.r.o. | Tento email dostáváš jako registrovaný člen Zara-club.\n"
            "Odhlásit se"
        ),
    },
    # N08
    {
        "subject": "Heureka.cz: Produkty na vašem watchlistu jsou nyní levnější",
        "body": (
            "Dobrý den,\n\n"
            "cena produktů, které sledujete, klesla:\n\n"
            "• Dyson V15 Detect — z 14 990 Kč na 12 490 Kč (-17 %)\n"
            "• Bosch WAX32EH0BY pračka — z 19 990 Kč na 17 490 Kč (-12 %)\n\n"
            "Porovnat nabídky → heureka.cz\n\n"
            "Heureka Group a.s. | Notifikaci jsi nastavil ve svém profilu. Vypnout."
        ),
    },
    # N09
    {
        "subject": "Dr. Max: Připomínáme vaši věrnostní slevu 10 % — platnost do konce týdne",
        "body": (
            "Dobrý den,\n\n"
            "váš věrnostní kupón na slevu 10 % vyprší v neděli 27. dubna.\n\n"
            "Kód: VERNOST10\n"
            "Platí na celý sortiment v e-shopu i v lékárnách Dr. Max.\n\n"
            "Uplatnit slevu → drmax.cz\n\n"
            "Dr. Max Lékárna s.r.o. | Zasíláme registrovaným zákazníkům věrnostního programu.\n"
            "Odhlásit odběr"
        ),
    },
    # N10
    {
        "subject": "Datart: Jarní výprodej spotřební elektroniky — poslední kusy",
        "body": (
            "Ahoj,\n\n"
            "jarní výprodej se blíží ke konci a zbývají poslední kusy za skvělé ceny:\n\n"
            "📺 Smart TV 55\" 4K — 8 990 Kč (bylo 12 490 Kč)\n"
            "🎧 Sony WH-1000XM5 — 6 490 Kč (bylo 8 990 Kč)\n"
            "💻 HP laptop 15\" — 11 990 Kč\n\n"
            "Nakoupit → datart.cz\n\n"
            "Datart International a.s. | Dostáváš tyto emaily jako registrovaný zákazník.\n"
            "Odhlásit se od newsletteru"
        ),
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
    print(f"  ✓ {email_def['subject'][:65]}")


def main():
    print(f"Odesílám {len(TEST_EMAILS)} testovacích emailů na {TARGET}...\n")
    service = get_gmail_service()
    for i, email_def in enumerate(TEST_EMAILS):
        send_email(service, email_def)
        if i < len(TEST_EMAILS) - 1:
            time.sleep(5)
    print(f"\nHotovo — odesláno {len(TEST_EMAILS)} emailů.")
    print("Spusť agenta a zkontroluj výsledky v dashboardu.")


if __name__ == "__main__":
    main()
