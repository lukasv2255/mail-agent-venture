# Projekt 02 — Servisní firma / IMAP / Web dashboard schválení

---

## Kontext klienta

**Firma:** Malá autoservisní dílna (3 zaměstnanci, 1 recepční)
**E-mail systém:** Firemní e-mail na vlastní doméně přes IMAP (`info@autoservis-novak.cz` na Wedosu)
**Objem e-mailů:** ~15 příchozích denně, z toho ~10 jsou rezervace a dotazy na ceny
**Support tým:** Recepční odpovídá ručně mezi příjmem zákazníků — nestíhá, zapomíná
**Hlavní problém:** Zákazníci pošlou dotaz, nedostanou odpověď a zavolají konkurenci

---

## Co agent řeší

| Typ e-mailu                | Akce agenta           | Schválení     |
| -------------------------- | --------------------- | ------------- |
| Dotaz na cenu / dostupnost | Odpověď z ceníku v KB | Web dashboard |
| Rezervace termínu          | Potvrzení + instrukce | Web dashboard |
| Zrušení / přesun termínu   | Potvrzení zrušení     | Web dashboard |
| Dotaz na stav opravy       | Eskaluje na recepční  | —             |
| Stížnost / reklamace       | Eskaluje na recepční  | —             |
| Spam / neznámé             | Ignoruje              | —             |

---

## Simulace průběhu objednávky (s komplikacemi)

### Den 1 — Zákazník poptá termín

Zákazník Karel Svoboda napíše: _"Dobrý den, potřebuji výměnu brzd na Škoda Octavia, máte volný termín příští týden?"_

**Co agent udělá:**

1. Klasifikuje jako `rezervace_terminu`
2. Z KB načte: výměna brzd = 2–3 hodiny, cena od 2 500 Kč, volné termíny dle konfigurace
3. Sestaví odpověď s dostupnými termíny a cenou, pošle do web dashboardu
4. Recepční klikne Schválit na dashboardu
5. Karel dostane odpověď do 30 minut

**Komplikace č. 1 — IMAP App Password**
Wedos nevyžaduje OAuth2 — funguje na heslo. Ale majitel omylem změní heslo na e-mailu. Agent přestane číst poštu, Railway logy hlásí `IMAP authentication failed`.

→ Řešení: monitoring — agent pošle Telegram upozornění pokud se nepodaří připojit k IMAP. Heslo uloženo v Railway env `IMAP_PASSWORD`, aktualizovat tam.

### Den 2 — Karel potvrdí termín

Karel odpoví: _"Výborně, hodí se mi středa 14:00."_

**Co agent udělá:**
Klasifikuje jako `rezervace_terminu` (follow-up). Sestaví potvrzení termínu, adresu dílny, co přinést (TP, klíče od auta).

**Komplikace č. 2 — agent nezná aktuální obsazenost**
KB říká "středa je volná", ale recepční mezitím přijala telefonickou rezervaci na 14:00. Agent potvrdí termín který je obsazený.

→ Řešení: krátkodobě — dashboard zobrazuje upozornění "Zkontroluj kalendář před schválením". Dlouhodobě — napojit na Google Calendar nebo jednoduchý booking systém.

### Den 4 — Karel zruší termín

_"Omlouvám se, středa mi nevyšla, musím zrušit."_

Agent klasifikuje jako `zruseni_terminu`, sestaví potvrzení zrušení + nabídne nový termín. Recepční schválí.

**Komplikace č. 3 — recepční je na dovolené, dashboard nikdo neotvírá**
Drafty se hromadí ve frontě neschválených odpovědí. Karel 3 dny nečeká na potvrzení zrušení.

→ Řešení: pokud draft čeká déle než 2 hodiny bez schválení, agent pošle Telegram notifikaci jako zálohu: _"⚠ 3 neschválené drafty čekají na odpověď."_

### Den 5 — Stížnost na předchozí opravu

Jiný zákazník: _"Minulý měsíc jste mi opravili auto a teď to zase dělá stejný problém, tohle je nepřijatelné."_

Klasifikace: eskalační klíčové slovo `nepřijatelné` → agent nereaguje zákazníkovi, ale pošle Telegram: _"⚠ Eskalace: stížnost od zakaznik@email.cz — vyžaduje ruční odpověď."_

---

## Technická konfigurace

**Mail client:** `src/mail_client_imap.py`
**Notifier:** Web dashboard (FastAPI + jednoduchá HTML stránka)
**Deployment model:** Agent + dashboard běží na vývojářově Railway jako jeden service
**DRY_RUN:** `true` po dobu testování

**Env proměnné:**

```
IMAP_HOST=imap.wedos.net
IMAP_PORT=993
IMAP_USER=info@autoservis-novak.cz
IMAP_PASSWORD=...
SMTP_HOST=smtp.wedos.net
SMTP_PORT=587
ANTHROPIC_API_KEY=...
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
DRY_RUN=true
CHECK_INTERVAL_MINUTES=20
DASHBOARD_SECRET=...
```

**Specifika IMAP nasazení:**

- Ověřit IMAP host a port u poskytovatele (Wedos: `imap.wedos.net:993`)
- App Password nebo běžné heslo — záleží na poskytovateli
- Gmail a Outlook IMAP vyžadují OAuth2 nebo App Password, ne běžné heslo

---

## Delivery plán

| Fáze           | Co se dělá                                         | Kdy      |
| -------------- | -------------------------------------------------- | -------- |
| 1. Setup       | IMAP přihlášení, Railway deploy, DRY_RUN           | Den 1    |
| 2. KB příprava | Ceník, instrukce pro zákazníky, adresy             | Den 1–2  |
| 3. Dashboard   | Zprovoznit web schválení                           | Den 2–3  |
| 4. Testování   | 10 testovacích e-mailů přes druhý účet             | Den 3–4  |
| 5. Shadow mode | Agent generuje drafty, recepční odpovídá paralelně | Den 5–12 |
| 6. Vyhodnocení | Kolik % draftů bylo správných? Kde se agent mýlil? | Den 13   |
| 7. Produkce    | Zapnout nejdřív rezervace a dotazy na cenu         | Den 14   |

---

## Pricing

| Položka                       | Cena         |
| ----------------------------- | ------------ |
| Jednorázový setup + dashboard | 12 000 Kč    |
| Příprava KB (ceník, šablony)  | 2 000 Kč     |
| Měsíční provoz                | 1 800 Kč/měs |
| Úpravy                        | 500 Kč/hod   |

Vyšší setup fee oproti projektu 01 — kvůli web dashboardu a přípravě KB.

---

## Knowledge Base a učení agenta

### KB — čím víc firma dodá, tím líp agent odpovídá

Firma dodá ceník, seznam služeb, instrukce pro zákazníky → agent odpovídá přesně bez eskalace.
Uloženo v `prompts/` jako textové soubory.

**Co dodat pro projekt 02:**

- Kompletní ceník služeb (výměna brzd, oleje, pneumatik, klimatizace...)
- Otevírací doba, adresa, parkovací instrukce
- Postup rezervace a co zákazník musí přinést

### Zaměstnanci učí agenta tipy

Přes web dashboard — pole "Přidat tip agentovi":

```
Zákazníkům s Octavií vždy zmínit že nabízíme i diagnostiku zdarma při servisu.
Na dotazy na klimatizaci říct že sezóna je duben–červen, mimo sezónu delší čekací doba.
```

Agent uloží tip do `prompts/tips.md` a příště ho použije automaticky.

### Agent se učí z odpovědí

- Schválení → draft byl dobrý, uloží jako vzor
- Zamítnutí + oprava recepční → agent zaznamená rozdíl do `prompts/corrections.md`
- Opakované zamítání stejného typu → agent začne častěji čekat na schválení

---

## Chování při chybějící informaci

Když agent nedokáže odpovědět (dotaz mimo KB, neznámý termín, nestandardní požadavek), neeskaluje rovnou — nejdřív se pokusí situaci vyřešit sám nebo s pomocí klienta.

**Postup:**

1. Agent sestaví zprávu do web dashboardu s popisem problému:
   _"❓ Neznám odpověď na tento dotaz. Navrhuju: [návrh odpovědi / otázka na zákazníka]. Doplň chybějící info nebo uprav a schval."_

2. Klient má tři možnosti:
   - Napíše chybějící informaci do pole v dashboardu → agent vygeneruje nový draft a znovu zobrazí ke schválení
   - Schválí navržený draft beze změny
   - Zamítne a řeší ručně

3. Pokud klient nedoplní nic do 2 hodin → agent přeskočí a zaloguje jako `needs_human`.

**Příklad — projekt 02:**
Zákazník se ptá: _"Opravujete také klimatizace? A kolik to stojí?"_
KB klimatizace neobsahuje → agent zobrazí v dashboardu: _"❓ Klimatizace není v KB. Navrhuju zákazníkovi odpovědět: 'Ano, klimatizace opravujeme. Pro nacenění nás kontaktujte telefonicky.' Schválit nebo doplnit cenu?"_
Recepční doplní cenu → agent vygeneruje nový draft s cenou a zobrazí ke schválení.

---

## Správa po nasazení

- Dashboard dostupný na Railway URL, klient si záložuje do prohlížeče
- Vývojář monitoruje IMAP připojení — Railway logy + weekly check
- Při změně hesla e-mailu klient informuje vývojáře → update env proměnné na Railway
- KB (ceník, dostupné termíny) aktualizuje vývojář na vyžádání nebo klient přímo v prompts složce přes GitHub
