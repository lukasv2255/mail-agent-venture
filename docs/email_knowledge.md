# Co řeší zákaznická podpora přes e-mail

> Přehled pro každého — bez technického žargonu.
> Slouží jako základ pro konfiguraci mail agenta pro různé typy firem.
> Poslední aktualizace: 2026-04-13

---

## Jaké e-maily firmy dostávají?

Téměř každá firma dostává stejné typy e-mailů. Liší se jen podle toho, co prodává.

**E-shop** dostává hlavně:

- "Kde je moje objednávka?"
- "Chci vrátit zboží."
- "Je tenhle produkt správný pro mě?"
- "Pošlete mi fakturu."

**Softwarová firma** dostává hlavně:

- "Nefunguje mi přihlášení."
- "Chci zrušit předplatné."
- "Jak tohle nastavím?"

**Servisní firma** (kadeřník, řemeslník, poradce) dostává:

- "Kolik to stojí?"
- "Máte volný termín?"
- "Chci zrušit rezervaci."

---

## Jak firmy odpovídají — podle velikosti?

**Malá firma** — jeden člověk, Gmail, odpovídá ručně, někdy pozdě. Žádný systém, e-maily se ztrácejí.

**Střední firma** — ticketovací systém (Freshdesk, Help Scout), více lidí, slib odpovědi do 4–8 hodin. Každý e-mail má číslo tiketu, je přiřazený konkrétnímu člověku.

**Velká firma** — automatizace, AI, odpověď přichází do hodiny. Složitější věci přebírá člověk. Fungují podle SLA (garantovaná doba odpovědi).

---

## Co jsou platformy jako Zendesk nebo Freshdesk?

Jsou to nástroje, které firma koupí místo toho, aby programovala vlastní systém.

**Problém bez platformy:**
Firma dostane 100 e-mailů denně. Všechny chodí do jednoho Gmailu. Nikdo neví kdo na co odpověděl, e-maily se ztrácejí, zákazník čeká týden.

**Co platforma vyřeší:**
Každý e-mail se stane "tiketem" s číslem. Vidíš kdo na co odpovídá, jak dlouho to čeká, jestli je to vyřešené. Jako Jira nebo Trello, ale pro zákaznický support.

**Přehled platforem:**

| Nástroj            | Pro koho          | Co umí navíc                        | Cena                |
| ------------------ | ----------------- | ----------------------------------- | ------------------- |
| **Zendesk**        | Velké firmy       | Vše — SLA, AI, reporty              | ~$19/agent/měs      |
| **Freshdesk**      | Střední firmy     | Snadné nastavení, AI Freddy         | Zdarma do 10 agentů |
| **HubSpot**        | CRM firmy         | Propojení s marketingem             | Zdarma základní     |
| **Help Scout**     | Malé týmy         | Vypadá jako Gmail, jednoduché       | $25/uživatel/měs    |
| **Intercom**       | SaaS startupy     | Live chat + AI bot                  | $74/měs             |
| **Gorgias**        | E-shopy (Shopify) | Vidíš objednávku hned vedle e-mailu | $60/měs             |
| **Gmail + Zapier** | Mikrofirmy        | Žádná extra cena                    | $0 + Zapier         |

---

## Co zvládne AI samo — a co ne?

**AI zvládne bez pomoci:**

- Stav objednávky (zákazník napíše číslo, AI odpoví)
- Kde je zásilka (odkaz na sledování)
- Jak vrátit zboží (pošle instrukce)
- Kopie faktury
- Odpovědi na časté dotazy (otevírací doba, ceny, parametry produktu)
- Potvrzení přijetí e-mailu

**AI musí přivolat člověka:**

- Zákazník je naštvaný nebo píše emocionálně
- Píše o advokátovi, soudu, podvodu nebo GDPR
- Situace je neobvyklá a AI si není jistá
- Jde o důležitého klienta (VIP)
- Požadavek přesahuje pravomoci agenta (refund nad limit, výjimka z pravidel)

---

## Šablony odpovědí

### Stav objednávky

```
Dobrý den {jméno zákazníka},

děkujeme za Vaši objednávku #{číslo} ze dne {datum}.

Aktuální stav: {stav}
Sledování zásilky: {odkaz}
Odhadované doručení: {datum doručení}

S pozdravem,
Zákaznická podpora
```

### Potvrzení přijetí (auto-reply)

```
Dobrý den,

Váš e-mail jsme přijali a budeme se mu věnovat nejpozději do {lhůta}.
Číslo Vašeho požadavku: #{číslo tiketu}

S pozdravem,
Zákaznická podpora
```

### Vrácení zboží

```
Dobrý den {jméno zákazníka},

rozumíme, že si přejete vrátit objednávku #{číslo}.

Postup:
1. Zabalte zboží do původního obalu
2. Přiložte vyplněný formulář: {odkaz}
3. Zašlete na adresu: {adresa}

Refund zpracujeme do 5–7 pracovních dní.

S pozdravem,
Zákaznická podpora
```

### Předání člověku (eskalace)

```
Dobrý den {jméno zákazníka},

Váš požadavek předáváme specializovanému týmu, který se Vám ozve do {lhůta}.
Číslo požadavku: #{číslo tiketu}

S pozdravem,
Zákaznická podpora
```

---

## Kdo zpracovává maily — ty nebo klient?

Tohle je klíčová otázka před každým projektem.

**Varianta A — ty provozuješ agenta za klienta**
Agent běží na tvém Railway účtu, přistupuješ ke klientově e-mailu. Ty vidíš obsah zpráv jeho zákazníků.

- Klient ti musí dát přístup (OAuth nebo API token)
- Ty vidíš citlivá data — objednávky, reklamace, osobní údaje zákazníků
- Pokud dojde k úniku dat, jsi zodpovědný ty
- Vhodné pro: testování, portfolio, demonstrace

**Varianta B — klient si nasadí agenta sám**
Ty dodáš kód, klient si ho nasadí na svůj Railway nebo server. Ty nevidíš žádná data.

- Klient má plnou kontrolu nad svými daty
- Toto je správný model pro reálné nasazení u klienta

---

## Bezpečnost — základní pravidla

**API klíče a credentials**
Vždy v Railway env proměnných — nikdy v kódu ani v repozitáři. Gmail `credentials.json` a `token.json` nesmí být commitnuty na GitHub.

**Schválení odpovědí**
Proto existuje `/yes` / `/no` flow. Nikdy nespouštěj `auto-send` bez otestování na reálných datech.

**Logování**
Agent loguje předměty a odesílatele. Celé tělo e-mailu do logů nepatří — může obsahovat osobní údaje zákazníků.

**GDPR**
Pokud agent zpracovává e-maily zákazníků klienta, jsi **zpracovatel osobních údajů**. Klient musí mít s tebou zpracovatelskou smlouvu (DPA). Tohle řeší právník, ne kód.

---

## Proč je to důležité pro tento projekt?

Mail agent který stavíme dělá přesně tohle — automaticky čte e-maily, rozhodne jestli umí odpovědět, napíše odpověď a čeká na schválení. Tato znalostní báze říká, **pro jaké typy firem** a **jaké typy e-mailů** to dává smysl — a kde je potřeba člověk.

Oproti hotovým platformám (Zendesk, Gorgias...) je naše řešení levnější a přizpůsobitelné konkrétní firmě. Nevyžaduje měsíce nastavování.
