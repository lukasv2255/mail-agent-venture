# src/

Produkční kód agenta. Tyto soubory běží v produkci na Railway.

## Moduly (`modules/`)

| Soubor                  | Popis                                                 |
| ----------------------- | ----------------------------------------------------- |
| `modules/responder.py`  | Klasifikace + draft odpovědi + Telegram schválení     |
| `modules/sorter.py`     | IMAP třídění inboxu (IDLE / polling)                  |
| `modules/newsletter.py` | Týdenní newsletter — scraping + generování + odeslání |

## Mail klienti

| Soubor                    | Popis                                                    |
| ------------------------- | -------------------------------------------------------- |
| `mail_client.py`          | Abstrakce — přepíná implementaci podle `MAIL_CLIENT` env |
| `mail_client_imap.py`     | IMAP/SMTP (Seznam, iCloud, vlastní server)               |
| `mail_client_gmail.py`    | Gmail API (OAuth2)                                       |
| `mail_client_graph.py`    | Microsoft Graph (Outlook / Office 365)                   |
| `mail_client_helpdesk.py` | Zendesk / Freshdesk                                      |

## Ostatní

| Soubor            | Popis                                                       |
| ----------------- | ----------------------------------------------------------- |
| `classifier.py`   | Klasifikace emailů — načítá `prompts/classifier_prompt.txt` |
| `responder.py`    | Generování draft odpovědí — načítá `prompts/response_*.txt` |
| `kb_loader.py`    | Načítání Knowledge Base z `prompts/` nebo databáze          |
| `notifier.py`     | Telegram notifikace, fronta schválení (/yes /no)            |
| `dashboard.py`    | FastAPI web dashboard na portu 8081                         |
| `gmail_client.py` | Nízkoúrovňová Gmail API logika (OAuth, fetch, send)         |
