# Projekt 01 — Responder / E-shop s doplňky stravy

**Odesílatel:** `newagent7878@gmail.com` (Gmail API)
**Příjemce / inbox agenta:** `johnybb11@seznam.cz` (IMAP seznam.cz)
**Testovací skript:** `scripts/send_test_emails.py`

---

## Testovací emaily a očekávaný výsledek

| ID  | Předmět                         | Klasifikace | Očekávaný výsledek                              |
| --- | ------------------------------- | ----------- | ----------------------------------------------- |
| T01 | Dotaz na objednávku 4471        | A1          | Odpověď: odesláno, tracking CZ847392011         |
| T02 | Kde je moje zásilka - obj. 2280 | A1          | Odpověď: v přípravě, expedice do 2 dnů          |
| T03 | Dotaz na protein                | B1          | Odpověď z KB: 24g bílkovin, živočišný původ     |
| T04 | Protein a diabetes              | B2          | Opatrná odpověď: doporučit konzultaci s lékařem |
| T05 | Chci vrátit zboží               | A2          | Instrukce k vrácení: zabalit, formulář, adresa  |
| T06 | Poškozený produkt - reklamace   | ESC         | Telegram eskalace, agent neodpovídá             |
| T07 | Objednávka 9999                 | A1          | Odpověď: objednávka nenalezena, ověř číslo      |
| T08 | Spolupráce — nabídka reklamy    | UNK         | Bez odpovědi, pouze zalogovat                   |
