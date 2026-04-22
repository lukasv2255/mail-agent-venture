# Mail Agent

Modulární e-mailový agent — klasifikuje příchozí emaily a automaticky odpovídá, třídí nebo generuje newsletter.

Spuštění: `python3 main.py`

Projekt je připravený jako template pro klientské instance. Cesty se počítají
z aktuálního checkoutu přes `src/config.py`; klientské hodnoty patří do `.env`.
Postup je v `docs/template_setup.md`.

Interaktivní vytvoření `.env` pro novou instanci:

```bash
python3 scripts/new_instance_wizard.py
```

---

## Moduly

### Responder (`MODULE_RESPONDER=true`)

Zpracovává příchozí emaily — klasifikuje typ, vygeneruje draft odpovědi a čeká na schválení přes Telegram.

- `/yes` → odešle draft zákazníkovi
- `/no` → email přeskočí
- Eskalace (ESC) a neznámé emaily (UNK) → Telegram notifikace, agent neodpovídá

### Sorter (`MODULE_SORTER=true`)

Třídí inbox — relevantní B2B nabídky ponechá, zbytek přesune do složky `others`.

- Stupeň 1: hlavičky (`List-Unsubscribe`, `List-ID`, `Precedence: bulk`) → MOVE bez AI
- Stupeň 2: GPT-4o-mini — je to osobní B2B nabídka? → KEEP nebo MOVE
- Připojení přes IMAP IDLE (push notifikace), fallback na polling každých 60s
- `/sort` → ručně setřídí existující INBOX; bere přečtené i nepřečtené, ale stav `seen/unseen` nemění

### Newsletter (`MODULE_NEWSLETTER=true`)

Generuje a odesílá týdenní newsletter (výchozí: pondělí 7:00).

- Sbírá aktuální obsah z webu (DuckDuckGo search + scraping)
- Generuje text přes OpenAI
- Odesílá sám sobě (klient dostane na vlastní adresu)
- `/newsletter` → odešle okamžitě bez čekání na plánovaný čas

---

## Mail klienti

| `MAIL_CLIENT` | Popis                                                  |
| ------------- | ------------------------------------------------------ |
| `gmail`       | Gmail API (OAuth2) — výchozí                           |
| `imap`        | Univerzální IMAP/SMTP (Seznam, iCloud, vlastní server) |

---

## Testování

Testovací emaily a očekávané výsledky jsou v `tests/`:

```
tests/
  responder/projekt_01/   — e-shop s doplňky stravy
  sorter/projekt_01/      — třídění B2B nabídek
  newsletter/             — (připraveno)
```
