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

| Typ e-mailu      | Akce agenta                                    | Schválení     |
| ---------------- | ---------------------------------------------- | ------------- |
| Stav objednávky  | Dohledá podle čísla, odpoví                    | Telegram /yes |
| Dotaz na produkt | Odpověď z produktové KB                        | Telegram /yes |
| Vrácení zboží    | Pošle instrukce                                | Telegram /yes |
| Reklamace        | Eskaluje na člověka                            | —             |
| Neúplný dotaz    | Navrhne odpověď nebo požádá klienta o doplnění | Telegram /yes |
| Spam / neznámé   | Ignoruje                                       | —             |

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

| Fáze           | Co se dělá                                             | Kdy      |
| -------------- | ------------------------------------------------------ | -------- |
| 1. Setup       | Gmail OAuth, Railway deploy, DRY_RUN test              | Den 1    |
| 2. Testování   | 10 testovacích e-mailů, kontrola klasifikace           | Den 2–3  |
| 3. Shadow mode | Agent generuje drafty, klient odpovídá ručně paralelně | Den 4–10 |
| 4. Vyhodnocení | Kolik % draftů bylo správných? Které typy zapnout?     | Den 11   |
| 5. Ladění      | Úprava promptů a KB dle výsledků shadow fáze           | Den 12   |
| 6. Produkce    | Zapnout odesílání nejdřív pro stav objednávky + FAQ    | Den 13   |

---

## Pricing

| Položka                               | Cena         |
| ------------------------------------- | ------------ |
| Jednorázový setup                     | 8 000 Kč     |
| Měsíční provoz (Railway + monitoring) | 1 500 Kč/měs |
| Úpravy promptů a pravidel             | 500 Kč/hod   |

---

## Knowledge Base a učení agenta

### KB — čím víc firma dodá, tím líp agent odpovídá

Firma dodá produktové listy, FAQ, reklamační řád → agent odpovídá přesně bez eskalace.
Uloženo v `prompts/` jako textové soubory. Při větším objemu → ChromaDB RAG.

**Co dodat pro projekt 01:**

- Složení a kontraindikace každého produktu
- FAQ (nejčastějších 20 dotazů s odpověďmi)
- Podmínky vrácení a reklamační řád

### Zaměstnanci učí agenta tipy

Přes Telegram příkaz `/learn`:

```
/learn Zákazníkům kteří zmiňují diabetes vždy doporučit konzultaci s lékařem.
/learn Nepoužívat slovo "bohužel" — nahradit neutrální formulací.
```

Agent uloží tip do `prompts/tips.md` a příště ho použije automaticky.

### Agent se učí z odpovědí

- `/yes` → draft byl dobrý, uloží jako vzor
- `/no` + klient napíše opravu → agent zaznamená rozdíl do `prompts/corrections.md`
- Opakované zamítání stejného typu → agent začne častěji žádat o schválení

---

## Chování při chybějící informaci

Když agent nedokáže odpovědět (chybí data v KB, neznámý dotaz, neobvyklá situace), neeskaluje rovnou — nejdřív se pokusí situaci vyřešit sám nebo s pomocí klienta.

**Postup:**

1. Agent sestaví Telegram zprávu s popisem problému:
   _"❓ Neznám odpověď na tento dotaz. Navrhuju: [návrh odpovědi / otázka na zákazníka]. Doplň chybějící info nebo uprav a schval."_

2. Klient má tři možnosti:
   - Napíše chybějící informaci přímo do Telegramu → agent vygeneruje nový draft s tou informací a znovu pošle ke schválení
   - Schválí navržený draft beze změny (`/yes`)
   - Zamítne a řeší ručně (`/no`)

3. Pokud klient nedoplní nic do 15 minut → agent přeskočí a zaloguje jako `needs_human`.

**Příklad — projekt 01:**
Zákazník se ptá: _"Můžu kombinovat váš protein s léky na štítnou žlázu?"_
Agent neví → pošle: _"❓ Zdravotní dotaz mimo KB. Navrhuju zákazníkovi odpovědět: 'Doporučujeme konzultaci s lékařem.' Schválit?"_
Klient odpoví `/yes` → zákazník dostane odpověď do 10 minut.

---

## Správa po nasazení

- Agent běží na vývojářově Railway — klient neřeší infrastrukturu
- Vývojář monitoruje Railway logy 1× týdně
- Klient hlásí problémy přes Telegram nebo e-mail
- Aktualizace promptů dle zpětné vazby: 1× za měsíc nebo na vyžádání
- Záloha credentials mimo repozitář (1Password nebo Railway secrets)
