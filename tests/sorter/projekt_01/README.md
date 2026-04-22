# Projekt 01 — Sorter / E-shop s doplňky stravy

**Odesílatel:** `newagent7878@gmail.com` (Gmail API)
**Příjemce / inbox agenta:** `johnybb11@seznam.cz` (IMAP seznam.cz)
**Rychlý batch skript:** `tests/sorter/projekt_01/test_sorter.py`
**Týdenní test:** `tests/sorter/projekt_01/run_week.py`

---

## Testovací emaily a očekávaný výsledek

### Spam (MOVE) — 12 emailů

| ID  | Předmět                                                      | Očekávaná klasifikace | Poznámka                               |
| --- | ------------------------------------------------------------ | --------------------- | -------------------------------------- |
| S01 | Váš web potřebuje SEO — zaručujeme 1. stránku Google         | MOVE                  | hromadná marketingová nabídka          |
| S02 | Získejte 10 000 nových sledujících na Instagramu za týden!   | MOVE                  | spam — růst followerů                  |
| S03 | Vydělávejte z domova 50 000 Kč měsíčně — bez zkušeností!     | MOVE                  | spam — práce z domova                  |
| S04 | URGENTNÍ: Váš bankovní účet byl dočasně omezen               | MOVE                  | phishing / podvodný email              |
| S05 | Investujte do kryptoměn — zaručený výnos 300 % ročně         | MOVE                  | spam — investiční podvod               |
| S06 | Pronájem databáze 50 000 ověřených B2B kontaktů              | MOVE                  | spam — prodej kontaktů                 |
| S07 | Máte nevyzvednutý balíček — potvrďte doručení                | MOVE                  | phishing / falešná zásilka             |
| S08 | Bezplatný audit vašeho webu — pouze dnes!                    | MOVE                  | spam — falešná urgence                 |
| S09 | Hromadné SMS a e-maily — získejte zákazníky levně            | MOVE                  | spam — nabídka rozesílacích služeb     |
| S10 | Zhubnete 10 kg za 30 dní — klinicky ověřeno                  | MOVE                  | spam — zdravotní produkt               |
| S11 | Vaše firma může získat dotaci až 2 000 000 Kč — zjistěte jak | MOVE                  | hromadná nabídka dotačního poradenství |
| S12 | Automatická odpověď: Jsem mimo kancelář do 28. dubna         | MOVE                  | automatická odpověď (out-of-office)    |

### Poptávky služby (KEEP) — 8 emailů

| ID  | Předmět                                                         | Očekávaná klasifikace | Poznámka                             |
| --- | --------------------------------------------------------------- | --------------------- | ------------------------------------ |
| P01 | Poptávka: IT služby pro naši firmu                              | KEEP                  | osobní B2B poptávka                  |
| P02 | Nabídka spolupráce — účetní a daňové služby pro vaši firmu      | KEEP                  | osobní nabídka spolupráce            |
| P03 | Zájem o vaše služby — rádi bychom se sešli                      | KEEP                  | osobní poptávka s doporučením        |
| P04 | Dodávka kancelářského nábytku — cenová nabídka                  | KEEP                  | adresovaná nabídka (hraniční případ) |
| P05 | Poptávka: vývoj e-shopu pro náš doplňkový sortiment             | KEEP                  | konkrétní zakázka, relevantní obor   |
| P06 | Zájem o marketingové služby — startup v oblasti healthtech      | KEEP                  | osobní poptávka na marketing         |
| P07 | Hledáme dodavatele pro rekonstrukci a vybavení nových kanceláří | KEEP                  | B2B poptávka s rozpočtem             |
| P08 | Spolupráce na vývoji mobilní aplikace — máme specifikaci        | KEEP                  | konkrétní zakázka, máme specifikaci  |

### E-shop newslettery (MOVE) — 10 emailů

Legitimní propagační emaily ze stránek, kde se uživatel registroval.
Nejde o spam v pravém slova smyslu, ale pro agenta jsou nerelevantní — nemají akční obsah.

| ID  | Předmět                                                                  | Očekávaná klasifikace | Poznámka                               |
| --- | ------------------------------------------------------------------------ | --------------------- | -------------------------------------- |
| N01 | Alza.cz: Velký jarní výprodej — slevy až 60 %                            | MOVE                  | e-shop newsletter — výprodej           |
| N02 | Mall.cz: Nové produkty a akční nabídky tohoto týdne                      | MOVE                  | e-shop newsletter — týdenní nabídky    |
| N03 | Sportisimo: Nová kolekce jaro 2025 + sleva 15 % pro tebe                 | MOVE                  | e-shop newsletter — slevový kód        |
| N04 | CZC.cz: Grafické karty a herní PC nyní za nejlepší ceny                  | MOVE                  | e-shop newsletter — naskladnění        |
| N05 | Notino.cz: Váš oblíbený parfém je znovu skladem                          | MOVE                  | wishlist notifikace                    |
| N06 | Rohlík.cz: Speciální nabídky na tento víkend                             | MOVE                  | e-shop newsletter — víkendové akce     |
| N07 | Zara: Exkluzivní přístup k nové kolekci — pouze pro členy                | MOVE                  | věrnostní program — early access       |
| N08 | Heureka.cz: Produkty na vašem watchlistu jsou nyní levnější              | MOVE                  | price drop notifikace                  |
| N09 | Dr. Max: Připomínáme vaši věrnostní slevu 10 % — platnost do konce týdne | MOVE                  | věrnostní kupón — expirační připomínka |
| N10 | Datart: Jarní výprodej spotřební elektroniky — poslední kusy             | MOVE                  | e-shop newsletter — výprodej           |

---

## Souhrn

| Kategorie          | Počet  | Očekávaná klasifikace |
| ------------------ | ------ | --------------------- |
| Spam               | 12     | MOVE                  |
| Poptávky služby    | 8      | KEEP                  |
| E-shop newslettery | 10     | MOVE                  |
| **Celkem**         | **30** |                       |

---

## Skripty

| Soubor           | Účel                                                                                              |
| ---------------- | ------------------------------------------------------------------------------------------------- |
| `test_sorter.py` | Odešle 30 testovacích emailů najednou — rychlý ruční test sorteru                                 |
| `run_week.py`    | Týdenní stability test — posílá ~100 emailů v průběhu 7 dní, monitoruje dashboard, generuje report |

### run_week.py

Spustíš jednou na začátku týdne, skript běží na pozadí celý týden sám.

```bash
# Spuštění — 7 dní, ~100 emailů
python3 tests/sorter/projekt_01/run_week.py

# Rychlý test — 20 emailů za 30 minut
python3 tests/sorter/projekt_01/run_week.py --fast

# Report z existujících logů
python3 tests/sorter/projekt_01/run_week.py --report
```

**Co dělá:**

- Posílá emaily ze šablon `SPAM`, `INQUIRY`, `NEWSLETTER` s realistickými váhami
- Očekává `SPAM -> MOVE`, `INQUIRY -> KEEP`, `NEWSLETTER -> MOVE`
- Každou minutu pinguje dashboard `/api/status` — detekuje pád agenta
- Loguje testovací běh do `logs/sorter/week_sent.jsonl` a `logs/sorter/uptime.jsonl`
- Čte rozhodnutí sorteru z `logs/sorter/sorter.jsonl`
- Na konci nebo po Ctrl+C vypíše report a uloží ho do `logs/sorter/week_report.txt`
