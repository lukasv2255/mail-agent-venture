# Projekt 03 — B2B distributor / Outlook (Microsoft Graph) / Slack schválení

---

## Kontext klienta

**Firma:** Malý distributor kancelářského vybavení (8 zaměstnanců, firemní Office 365)
**E-mail systém:** Outlook / Office 365 (`objednavky@kancelar-distribuce.cz`)
**Objem e-mailů:** ~40 příchozích denně — objednávky od odběratelů, dotazy na skladovost, faktury
**Support tým:** 2 obchodní zástupci sdílí mailbox, odpovídají ručně, bez systému
**Hlavní problém:** Dotazy na skladovost a stav objednávky zabírají 60 % času, opakují se každý den

---

## Co agent řeší

| Typ e-mailu                   | Akce agenta                     | Schválení      |
| ----------------------------- | ------------------------------- | -------------- |
| Dotaz na skladovost produktu  | Odpověď z KB skladu             | Slack tlačítko |
| Stav objednávky / expedice    | Odpověď z objednávkové KB       | Slack tlačítko |
| Žádost o fakturu / dobropis   | Eskaluje na účetní              | —              |
| Nová objednávka od odběratele | Potvrzení přijetí               | Slack tlačítko |
| Reklamace / chybná zásilka    | Eskaluje na obchodního zástupce | —              |
| Neznámé / obecné              | Ignoruje                        | —              |

---

## Simulace průběhu objednávky (s komplikacemi)

### Den 1 — Odběratel pošle objednávku

Firma ABC s.r.o. pošle e-mail: _"Dobrý den, objednáváme 50 ks kancelářských židlí REF-7821 a 20 ks stolů REF-3302. Potřebujeme dodat do 14 dnů."_

**Co agent udělá:**

1. Klasifikuje jako `nova_objednavka`
2. Sestaví potvrzení přijetí objednávky s výčtem položek a odhadovaným termínem
3. Pošle do Slack kanálu `#support-agent` se dvěma tlačítky: **Schválit** / **Zamítnout**
4. Obchodní zástupce klikne Schválit
5. ABC s.r.o. dostane potvrzení do 20 minut

**Komplikace č. 1 — Azure app registration**
Microsoft Graph vyžaduje registraci aplikace v Azure portálu. Klient nemá IT oddělení, neví co je Azure. Vývojář musí provést setup sám nebo navést klienta krok za krokem.

→ Řešení: vývojář provede Azure app registration a nastaví `client_id`, `client_secret`, `tenant_id` do Railway env proměnných. Klient nedělá nic technického.

### Den 3 — Dotaz na skladovost

Jiný odběratel: _"Máte na skladě 100 ks tiskárny HP LaserJet 4002? Potřebujeme znát dostupnost do zítřka."_

**Co agent udělá:**

1. Klasifikuje jako `dotaz_skladovost`
2. Z KB načte: HP LaserJet 4002 = 35 ks skladem
3. Sestaví odpověď: 35 ks dostupných, zbývajících 65 ks na cestě, ETA 10 dní
4. Slack notifikace → obchodní zástupce schválí

**Komplikace č. 2 — KB skladu je zastaralá**
Agent odpoví "35 ks skladem", ale skutečný stav je 12 ks (mezitím přišla velká objednávka). Odběratel počítá se 35 ks, vzniká problém.

→ Řešení: KB skladu označit datem poslední aktualizace. Agent přidá do odpovědi: _"Stav skladu k [datum]. Pro závazné potvrzení kontaktujte obchodního zástupce."_ Dlouhodobě — napojit na ERP nebo skladový systém přes API.

### Den 5 — Objednávka je zpožděná

ABC s.r.o. píše: _"Objednávka z pondělí ještě nedorazila, původně jste psali 14 dní. Jsme v pátek, tedy den 5. Kdy to bude?"_

**Co agent udělá:**
Klasifikuje jako `stav_objednavky`, sestaví odpověď se stavem expedice z KB.

**Komplikace č. 3 — e-mail přišel mimo pracovní dobu**
Agent běží 24/7, sestaví draft v sobotu ve 22:00 a Slack notifikaci nikdo nevidí. Draft čeká do pondělí.

→ Řešení: pro e-maily mimo pracovní dobu (Po–Pá 8–17) agent sestaví draft a uloží, ale Slack notifikaci pošle až v 8:00 pondělí. Přidat `BUSINESS_HOURS_ONLY_NOTIFY=true` do konfigurace.

### Den 7 — Faktura

Účetní z ABC s.r.o.: _"Prosím o zaslání faktury č. 2026-0441 a dobropisu k předchozí objednávce."_

Klasifikace: `faktura_dobropis` → agent eskaluje, pošle Slack upozornění: _"📋 Žádost o fakturu od ABC s.r.o. — předat účetní."_

**Komplikace č. 4 — Slack notifikace jde do špatného kanálu**
Agent posílá vše do `#support-agent`, ale faktury má řešit účetní v `#ucetnictvi`. Obchodní zástupce to musí přeposílat ručně.

→ Řešení: routing podle typu e-mailu — `faktura_dobropis` → `#ucetnictvi`, ostatní → `#support-agent`. Přidat `SLACK_CHANNEL_BILLING` env proměnnou.

---

## Technická konfigurace

**Mail client:** `src/mail_client_graph.py`
**Notifier:** Slack (Slack API, interaktivní tlačítka)
**Deployment model:** Agent běží na vývojářově Railway
**DRY_RUN:** `true` po dobu testování

**Env proměnné:**

```
GRAPH_CLIENT_ID=...
GRAPH_CLIENT_SECRET=...
GRAPH_TENANT_ID=...
GRAPH_USER_EMAIL=objednavky@kancelar-distribuce.cz
ANTHROPIC_API_KEY=...
SLACK_BOT_TOKEN=...
SLACK_CHANNEL_SUPPORT=#support-agent
SLACK_CHANNEL_BILLING=#ucetnictvi
DRY_RUN=true
CHECK_INTERVAL_MINUTES=15
BUSINESS_HOURS_ONLY_NOTIFY=true
```

**Specifika Microsoft Graph nasazení:**

1. Azure Portal → App registrations → New registration
2. Přidat API permissions: `Mail.Read`, `Mail.Send`, `Mail.ReadWrite`
3. Vytvořit Client secret (platnost max. 2 roky — nastavit připomenutí obnovy)
4. Zaznamenat: `Application (client) ID`, `Directory (tenant) ID`, `Client secret value`
5. Nastavit do Railway env proměnných

**Důležité:** Client secret expiruje. Nastavit kalendářní připomenutí 1 měsíc před expirací.

---

## Delivery plán

| Fáze                  | Co se dělá                                | Kdy     |
| --------------------- | ----------------------------------------- | ------- |
| 1. Azure setup        | App registration, permissions, secret     | Den 1   |
| 2. Slack setup        | Slack app, bot token, kanály              | Den 1   |
| 3. Railway deploy     | Env proměnné, DRY_RUN test                | Den 2   |
| 4. KB příprava        | Skladovost, produkty, objednávkový proces | Den 2–3 |
| 5. Testování          | 10 testovacích e-mailů                    | Den 3–4 |
| 6. Slack routing      | Nastavit různé kanály pro různé typy      | Den 4   |
| 7. Schválení klientem | Obchodní zástupce testuje Slack schválení | Den 5–6 |
| 8. Produkce           | DRY_RUN=false                             | Den 7   |

Delší delivery oproti projektům 01 a 02 — kvůli Azure setup a složitějšímu routingu.

---

## Pricing

| Položka                                     | Cena         |
| ------------------------------------------- | ------------ |
| Jednorázový setup (Azure + Slack + routing) | 15 000 Kč    |
| Příprava KB (sklad, produkty, procesy)      | 3 000 Kč     |
| Měsíční provoz                              | 2 000 Kč/měs |
| Úpravy                                      | 500 Kč/hod   |
| Obnova Azure Client secret (1× za 2 roky)   | 500 Kč       |

Nejvyšší setup fee ze všech tří projektů — Azure registrace a Slack integrace jsou složitější.

---

## Správa po nasazení

- Vývojář nastaví kalendářní připomenutí na obnovu Azure Client secret (každé 2 roky)
- Klient informuje vývojáře při změně organizační struktury (nový Slack kanál, nový zodpovědný)
- KB skladu aktualizuje vývojář nebo klient přímo — dohodnout proces
- Vývojář monitoruje Railway logy 1× týdně, Graph API rate limity
- Při výpadku Microsoft 365 → agent loguje chybu + Telegram fallback notifikace
