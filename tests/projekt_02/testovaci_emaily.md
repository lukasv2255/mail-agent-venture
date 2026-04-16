# Testovací e-maily — Projekt 02 (Autoservis)

> Pošli ze druhého e-mailového účtu na info@autoservis-novak.cz (nebo testovací IMAP inbox).
> Každý e-mail testuje jiný typ a hraniční případ.

---

## T01 — Dotaz na cenu (v KB)

**Předmět:** Cena výměny brzd
**Tělo:**

```
Dobrý den,
kolik stojí výměna předních brzd na Škoda Octavia 2019?
Děkuji
```

**Očekávaný výsledek:** Agent odpoví z KB — od 2 500 Kč, cca 2 hodiny.

---

## T02 — Rezervace termínu

**Předmět:** Rezervace — výměna oleje
**Tělo:**

```
Dobrý den,
chtěl bych si rezervovat výměnu oleje na příští týden.
Mám VW Passat 2020, diesel.
Je možný termín v úterý ráno?
Pavel Čermák
```

**Očekávaný výsledek:** Agent nabídne volné termíny z KB (Út 21.4.: 9:00, 13:00), požádá o potvrzení.

---

## T03 — Zrušení rezervace

**Předmět:** Zrušení termínu
**Tělo:**

```
Dobrý den,
bohužel musím zrušit svoji rezervaci REZ-001 na pondělí 20.4.
Mohu si přeobjednat na středu?
Karel Svoboda
```

**Očekávaný výsledek:** Agent potvrdí zrušení REZ-001 a nabídne středu 22.4. 8:00 nebo 11:00.

---

## T04 — Dotaz na službu mimo KB (doplnění od klienta)

**Předmět:** Opravujete klimatizace?
**Tělo:**

```
Dobrý den,
opravujete také klimatizace? A kolik přibližně stojí plnění chladiva?
```

**Očekávaný výsledek:** Agent odpoví z KB — plnění klimatizace od 1 200 Kč, sezóna duben–červen.

---

## T05 — Dotaz na stav opravy (eskalace)

**Předmět:** Kdy bude hotové auto?
**Tělo:**

```
Dobrý den,
přivezl jsem auto dnes ráno na opravu brzd, už jsou to 4 hodiny.
Kdy bude hotové?
Tomáš Dvořák
```

**Očekávaný výsledek:** Agent eskaluje — stav probíhající opravy nezná, předá recepční.

---

## T06 — Reklamace (eskalace)

**Předmět:** Reklamace opravy
**Tělo:**

```
Dobrý den,
minulý měsíc jste mi měnili brzdy a teď při brzdění slyším nepříjemný zvuk.
Toto je nepřijatelné, chci okamžitou nápravu.
Alena Marková
```

**Očekávaný výsledek:** Agent eskaluje (klíčová slova: "nepřijatelné", "reklamace"). Upozornění pro recepční.

---

## T07 — Dotaz na otevírací dobu

**Předmět:** Otevírací doba
**Tělo:**

```
Dobrý den, máte v sobotu otevřeno?
```

**Očekávaný výsledek:** Agent odpoví z KB — So 8:00–12:00.

---

## T08 — Nesouvisející e-mail

**Předmět:** Nabídka pojištění vozidel
**Tělo:**

```
Dobrý den, nabízíme výhodné pojištění pro autoservisy. Máte zájem?
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
