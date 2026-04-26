# Responder — E-shop s doplňky stravy

**Odesílatel:** účet přihlášený přes Gmail API
**Příjemce / inbox agenta:** hodnota `TEST_TARGET_EMAIL` nebo `GMAIL_ADDRESS` v `.env`

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

## Skripty

| Soubor              | Účel                                                     |
| ------------------- | -------------------------------------------------------- |
| `test_responder.py` | Odešle 8 testovacích emailů najednou — rychlý ruční test |

Pro týdenní stability test použij `tests/run_mixed_week.py` v rootu — pokrývá sorter, responder i email_body dohromady.
