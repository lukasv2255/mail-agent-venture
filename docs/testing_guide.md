# Testovací průvodce — Mail Agent

Jak testovat agenta lokálně: posílání testovacích mailů, sledování reakcí v Telegramu, vyhodnocení výsledků.

---

## Jak posílat testovací emaily

Vždy použij `EmailMessage` (ne `MIMEText`) a **nenastavuj `From` header** — jinak se ztratí subject:

```python
import sys, base64
from email.message import EmailMessage
sys.path.insert(0, 'src')
from gmail_client import get_gmail_service

service = get_gmail_service()
msg = EmailMessage()
msg['To'] = 'newagent7878@gmail.com'
msg['Subject'] = 'Předmět emailu'
msg.set_content('Tělo emailu...')

raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
service.users().messages().send(userId='me', body={'raw': raw}).execute()
```

Spusť z kořene projektu: `python3 -c "..."` nebo ze skriptu v `tests/`.

---

## Testovací scénáře — Projekt 01 (E-shop)

Viz `tests/projekt_01/testovaci_emaily.md` pro plná znění emailů.

| Test | Předmět                         | Očekávaná klasifikace | Akce agenta                                           |
| ---- | ------------------------------- | --------------------- | ----------------------------------------------------- |
| T01  | Dotaz na objednavku 4471        | A1                    | Draft odpovědi → Telegram ke schválení                |
| T02  | Kde je moje zásilka - obj. 2280 | A1                    | Draft odpovědi → Telegram ke schválení                |
| T03  | Dotaz na protein                | B1                    | Draft odpovědi → Telegram ke schválení                |
| T04  | Protein a diabetes              | B2                    | Draft odpovědi (opatrný) → Telegram ke schválení      |
| T05  | Chci vratit zbozi               | A2                    | Draft s instrukcemi k vrácení → Telegram ke schválení |
| T06  | Poskozeny produkt - reklamace   | ESC                   | 🚨 Telegram notifikace, žádný auto-reply              |
| T07  | Objednávka 9999                 | A1                    | Draft "objednávka nenalezena" → Telegram ke schválení |
| T08  | Spolupráce — nabídka reklamy    | UNK                   | ⚪ Telegram log, žádná akce                           |

**Cíl:** 6 auto-reply (T01–T05, T07) + 1 ESC (T06) + 1 UNK (T08)

---

## Postup testování

1. **Spusť agenta** — `python3 main.py`
2. **Pošli testovací mail** (viz kód výše nebo skript níže)
3. **Spusť `/check`** v Telegramu (chat Mail-agent Mac)
4. **Sleduj Telegram reakci:**
   - `🔍 Spouštím check emailů...` → agent příjal příkaz
   - Pro A1–B2: přijde návrh odpovědi s `/yes` / `/no`
   - Pro ESC: přijde `🚨 Eskalace` s textem emailu
   - Pro UNK: přijde `⚪ Nezpracováno`
   - Pokud žádné maily: `📭 Žádné nové emaily.`
5. **Odpověz `/yes`** (odešle email) nebo `/no` (přeskočí)

---

## Skript pro hromadné odeslání testů

```python
# tests/send_test_emails.py
import sys, base64
from email.message import EmailMessage
sys.path.insert(0, 'src')
from gmail_client import get_gmail_service

TESTS = [
    ("Dotaz na objednavku 4471",
     "Dobrý den, chtěl bych se zeptat, kdy dorazí moje objednávka číslo 4471. Děkuji, Jan Novák"),

    ("Kde je moje zasilka - obj. 2280",
     "Dobrý den, objednala jsem kreatin, objednávka č. 2280. Ještě jsem nedostala žádnou informaci o odeslání. Eva Kovářová"),

    ("Dotaz na protein",
     "Dobrý den, zajímá mě Whey Protein Vanilka. Kolik obsahuje bílkovin na porci a je vhodný pro vegetariány?"),

    ("Protein a diabetes",
     "Dobrý den, mám diabetes 2. typu a rád bych začal užívat váš protein. Je to bezpečné?"),

    ("Chci vratit zbozi",
     "Dobrý den, obdržel jsem objednávku 4471 ale protein mi nechutná, chci ho vrátit. Jak mám postupovat? Jan Novák"),

    ("Poskozeny produkt - reklamace",
     "Dobrý den, objednávka 1102 dorazila s poškozeným obalem a část obsahu byla rozsypaná. Toto je nepřijatelné, chci okamžitě náhradu nebo vrácení peněz. Jana Nováková"),

    ("Objednavka 9999",
     "Dobrý den, kdy dorazí objednávka číslo 9999?"),

    ("Spoluprace - nabidka reklamy",
     "Dobrý den, nabízíme reklamní plochy na fitness portálech. Máte zájem o spolupráci?"),
]

service = get_gmail_service()
for subject, body in TESTS:
    msg = EmailMessage()
    msg['To'] = 'newagent7878@gmail.com'
    msg['Subject'] = subject
    msg.set_content(body)
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    result = service.users().messages().send(userId='me', body={'raw': raw}).execute()
    print(f"Odesláno: {subject}")
```

Spuštění: `python3 tests/send_test_emails.py`

---

## Vyhodnocovací tabulka

Po každém testovacím běhu vyplň:

| Test | Klasifikace správná? | Telegram správný? | Odpověď správná? | Poznámka |
| ---- | -------------------- | ----------------- | ---------------- | -------- |
| T01  |                      |                   |                  |          |
| T02  |                      |                   |                  |          |
| T03  |                      |                   |                  |          |
| T04  |                      |                   |                  |          |
| T05  |                      |                   |                  |          |
| T06  |                      |                   |                  |          |
| T07  |                      |                   |                  |          |
| T08  |                      |                   |                  |          |

---

## Telegram příkazy

| Příkaz   | Akce                              |
| -------- | --------------------------------- |
| `/check` | Okamžitý check nových emailů      |
| `/yes`   | Schválit a odeslat návrh odpovědi |
| `/no`    | Přeskočit návrh odpovědi          |
