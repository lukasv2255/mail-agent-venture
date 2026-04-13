# Projekt 01 — E-shop / Gmail / Telegram schválení

---

## Kontext klienta

**Firma:** Malý e-shop s doplňky stravy (20–50 objednávek denně)
**E-mail systém:** Gmail (newagent7878@gmail.com jako vzor)
**Objem e-mailů:** ~30 příchozích denně, z toho ~20 opakovaných dotazů
**Support tým:** 1 člověk, odpovídá ručně, nestíhá
**Hlavní problém:** Zákazníci čekají na odpověď 1–2 dny, opakované dotazy zabírají 80 % času

---

## Co agent řeší

| Typ e-mailu      | Akce agenta                 | Schválení     |
| ---------------- | --------------------------- | ------------- |
| Stav objednávky  | Dohledá podle čísla, odpoví | Telegram /yes |
| Dotaz na produkt | Odpověď z produktové KB     | Telegram /yes |
| Vrácení zboží    | Pošle instrukce             | Telegram /yes |
| Reklamace        | Eskaluje na člověka         | —             |
| Spam / neznámé   | Ignoruje                    | —             |

---

## Simulace průběhu objednávky (s komplikacemi)

### Den 1 — Zákazník objedná

Zákazník Jan Novák objedná protein #ORD-4471. Automaticky dostane potvrzení z e-shopu (ne od agenta — to řeší e-shop). Agent nereaguje.

### Den 2 — Dotaz na stav

Jan napíše: _"Dobrý den, kdy dorazí moje objednávka číslo 4471?"_

**Co agent udělá:**

1. Přečte e-mail, klasifikuje jako `type_b` (stav objednávky)
2. Dohledá v testovací logice: 4471 je liché → odesláno, tracking ID: CZ847392011
3. Sestaví odpověď, pošle draft do Telegramu
4. Čeká max. 5 minut na /yes nebo /no
5. Po /yes odešle odpověď, označí e-mail jako zpracovaný

**Komplikace č. 1 — timeout**
Klient nestiskne /yes do 5 minut (byl na obědě). Agent e-mail přeskočí, zaloguje `approval_timeout`. Jan nedostane odpověď.

→ Řešení: agent pošle připomenutí po 4 minutách. Timeout prodloužit na 15 minut nebo přidat /remind příkaz.

### Den 3 — Jan píše znovu

_"Prosím o odpověď, objednávka 4471, kde je zásilka?"_

Agent opět klasifikuje, sestaví draft. Tentokrát klient schválí. Jan dostane odpověď se sledovacím číslem.

**Komplikace č. 2 — duplicitní zpracování**
Agent vidí oba e-maily (původní i follow-up) jako nezpracované, sestaví 2 drafty najednou. Klient dostane 2 Telegram notifikace.

→ Řešení: thread_id deduplikace — pokud vlákno už bylo zodpovězeno, přeskočit.

### Den 5 — Reklamace

Jan napíše: _"Protein dorazil poškozený, chci vrátit peníze, jinak půjdu na reklamaci."_

Klasifikace: obsahuje klíčové slovo `reklamace` → `unknown` → agent nereaguje, pouze interně zaloguje a označí jako zpracovaný.

**Komplikace č. 3 — zákazník čeká, nikdo neodpovídá**
Agent e-mail zpracoval (označil), ale člověk ho neviděl. Jan čeká 3 dny bez odpovědi.

→ Řešení: pro `unknown` s eskalačními klíčovými slovy agent pošle Telegram upozornění: _"⚠ Eskalace: reklamace od jan@email.cz — vyžaduje ruční odpověď."_

---

## Technická konfigurace

**Mail client:** `src/mail_client_gmail.py`
**Notifier:** Telegram (`/yes` / `/no`)
**Deployment model:** Agent běží na vývojářově Railway
**DRY_RUN:** `true` po dobu testování, pak `false`

**Env proměnné:**

```
GMAIL_CREDENTIALS_FILE=credentials.json
GMAIL_TOKEN_JSON=<base64>
GMAIL_ADDRESS=support@klient.cz
ANTHROPIC_API_KEY=...
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
DRY_RUN=true
CHECK_INTERVAL_MINUTES=30
```

---

## Delivery plán

| Fáze                  | Co se dělá                                   | Kdy     |
| --------------------- | -------------------------------------------- | ------- |
| 1. Setup              | Gmail OAuth, Railway deploy, DRY_RUN test    | Den 1   |
| 2. Testování          | 10 testovacích e-mailů, kontrola klasifikace | Den 2–3 |
| 3. Schválení klientem | Klient vidí drafty, dává zpětnou vazbu       | Den 4   |
| 4. Ladění             | Úprava promptů, eskalačních pravidel         | Den 5   |
| 5. Produkce           | DRY_RUN=false, reálné odesílání              | Den 6   |

---

## Pricing

| Položka                               | Cena         |
| ------------------------------------- | ------------ |
| Jednorázový setup                     | 8 000 Kč     |
| Měsíční provoz (Railway + monitoring) | 1 500 Kč/měs |
| Úpravy promptů a pravidel             | 500 Kč/hod   |

---

## Správa po nasazení

- Agent běží na vývojářově Railway — klient neřeší infrastrukturu
- Vývojář monitoruje Railway logy 1× týdně
- Klient hlásí problémy přes Telegram nebo e-mail
- Aktualizace promptů dle zpětné vazby: 1× za měsíc nebo na vyžádání
- Záloha credentials mimo repozitář (1Password nebo Railway secrets)
