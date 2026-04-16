# Testovací e-maily — Projekt 03 (B2B Distributor)

> Pošli ze druhého e-mailového účtu na objednavky@kancelar-distribuce.cz (nebo testovací inbox).
> Každý e-mail testuje jiný typ a hraniční případ.

---

## T01 — Nová objednávka

**Předmět:** Objednávka kancelářského vybavení
**Tělo:**

```
Dobrý den,
objednáváme 50 ks kancelářských židlí REF-7821 a 20 ks stolů REF-3302.
Potřebujeme dodat do 14 dnů.
IČO: 12345678, DIČ: CZ12345678
S pozdravem, Jan Kratochvíl, ABC s.r.o.
```

**Očekávaný výsledek:** Agent potvrdí přijetí objednávky, shrne položky a odhadovanou dodací lhůtu.

---

## T02 — Dotaz na skladovost

**Předmět:** Dostupnost HP LaserJet 4002
**Tělo:**

```
Dobrý den,
máte na skladě 100 ks tiskárny HP LaserJet 4002?
Potřebujeme znát dostupnost do zítřka.
Pavel Novotný, XYZ a.s.
```

**Očekávaný výsledek:** Agent odpoví z KB — 35 ks skladem, zbývajících 65 ks nelze potvrdit. Doporučí kontaktovat obchodního zástupce pro závazné potvrzení.

---

## T03 — Stav objednávky

**Předmět:** Kde je naše objednávka ORD-2041?
**Tělo:**

```
Dobrý den,
objednávku ORD-2041 jsme zadali před 3 dny, kdy očekávat dodání?
ABC s.r.o.
```

**Očekávaný výsledek:** Agent odpoví z KB — v přípravě, expedice do 5 pracovních dní.

---

## T04 — Dotaz na certifikaci (v KB)

**Předmět:** ISO certifikát
**Tělo:**

```
Dobrý den,
potřebujeme pro interní audit doložit vaši ISO certifikaci.
Můžete zaslat certifikát ISO 9001?
Procurement, Město Brno
```

**Očekávaný výsledek:** Agent odpoví z KB — číslo certifikátu CZ-ISO-2024-0471, platnost do 12/2026, nabídne přiložit certifikát.

---

## T05 — Žádost o fakturu (eskalace na účetní)

**Předmět:** Faktura k objednávce ORD-2038
**Tělo:**

```
Dobrý den,
prosíme o zaslání faktury k objednávce ORD-2038.
Potřebujeme dobropis k předchozí objednávce ORD-2030.
Účetní oddělení, XYZ a.s.
```

**Očekávaný výsledek:** Agent eskaluje do kanálu #ucetnictvi — faktura a dobropis mimo jeho kompetence.

---

## T06 — Reklamace (eskalace)

**Předmět:** Chybná zásilka — reklamace
**Tělo:**

```
Dobrý den,
objednávka ORD-2038 dorazila nekompletní — chybí 3 ks tiskáren.
Toto je nepřijatelné, požadujeme okamžité dořešení nebo vrácení peněz.
Pavel Novotný, XYZ a.s.
```

**Očekávaný výsledek:** Agent eskaluje (klíčová slova: "nepřijatelné", "reklamace"). Slack upozornění pro obchodního zástupce.

---

## T07 — Dotaz mimo KB (doplnění od zástupce)

**Předmět:** Dotaz na leasing kancelářského vybavení
**Tělo:**

```
Dobrý den,
nabízíte možnost leasingu nebo splátkového prodeje pro větší objednávky?
DEF s.r.o.
```

**Očekávaný výsledek:** Agent neví → pošle do Slacku: _"❓ Dotaz na leasing — není v KB. Navrhuju odpovědět: 'Tuto možnost aktuálně nenabízíme.' Doplnit nebo schválit?"_ Zástupce může doplnit aktuální info.

---

## T08 — Nesouvisející e-mail

**Předmět:** Nabídka SEO služeb
**Tělo:**

```
Dobrý den, nabízíme optimalizaci webu pro e-shopy. Zájem?
```

**Očekávaný výsledek:** Agent klasifikuje jako `unknown`, nereaguje, pouze zaloguje.

---

## Jak vyhodnotit výsledky

| Test | Klasifikace správná? | Odpověď správná? | Eskalace správná? | Poznámka |
| ---- | -------------------- | ---------------- | ----------------- | -------- |
| T01  |                      |                  |                   |          |
| T02  |                      |                  |                   |          |
| T03  |                      |                  |                   |          |
| T04  |                      |                  |                   |          |
| T05  |                      |                  |                   |          |
| T06  |                      |                  |                   |          |
| T07  |                      |                  |                   |          |
| T08  |                      |                  |                   |          |
