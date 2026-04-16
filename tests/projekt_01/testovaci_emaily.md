# Testovací e-maily — Projekt 01 (E-shop)

> Pošli ze druhého Gmail účtu na newagent7878@gmail.com.
> Každý e-mail testuje jiný typ a hraniční případ.

---

## T01 — Stav objednávky (odesláno, liché číslo)

**Předmět:** Dotaz na objednávku 4471
**Tělo:**

```
Dobrý den,
chtěl bych se zeptat, kdy dorazí moje objednávka číslo 4471.
Děkuji, Jan Novák
```

**Očekávaný výsledek:** Agent odpoví se stavem "odesláno" a tracking číslem CZ847392011.

---

## T02 — Stav objednávky (v přípravě, sudé číslo)

**Předmět:** Kde je moje zásilka - obj. 2280
**Tělo:**

```
Dobrý den,
objednala jsem kreatin, objednávka č. 2280. Ještě jsem nedostala žádnou informaci o odeslání.
Eva Kovářová
```

**Očekávaný výsledek:** Agent odpoví "v přípravě, expedice do 2 dnů".

---

## T03 — Dotaz na produkt (v KB)

**Předmět:** Dotaz na protein
**Tělo:**

```
Dobrý den,
zajímá mě Whey Protein Vanilka. Kolik obsahuje bílkovin na porci a je vhodný pro vegetariány?
```

**Očekávaný výsledek:** Agent odpoví z KB — 24g bílkovin, zmíní že je ze syrovátky (živočišný původ).

---

## T04 — Zdravotní dotaz (mimo KB → doplnění nebo opatrná odpověď)

**Předmět:** Protein a diabetes
**Tělo:**

```
Dobrý den,
mám diabetes 2. typu a rád bych začal užívat váš protein. Je to bezpečné?
```

**Očekávaný výsledek:** Agent neodpoví s jistotou — doporučí konzultaci s lékařem. Nebo požádá klienta o doplnění.

---

## T05 — Vrácení zboží

**Předmět:** Chci vrátit zboží
**Tělo:**

```
Dobrý den,
obdržel jsem objednávku 4471 ale protein mi nechutná, chci ho vrátit.
Jak mám postupovat?
Jan Novák
```

**Očekávaný výsledek:** Agent pošle instrukce k vrácení — zabalit, přiložit formulář, zaslat na adresu.

---

## T06 — Reklamace (eskalace)

**Předmět:** Poškozený produkt - reklamace
**Tělo:**

```
Dobrý den,
objednávka 1102 dorazila s poškozeným obalem a část obsahu byla rozsypaná.
Toto je nepřijatelné, chci okamžitě náhradu nebo vrácení peněz.
Jana Nováková
```

**Očekávaný výsledek:** Agent eskaluje (klíčová slova: "nepřijatelné", "reklamace"). Telegram upozornění pro klienta.

---

## T07 — Neznámá objednávka

**Předmět:** Objednávka 9999
**Tělo:**

```
Dobrý den, kdy dorazí objednávka číslo 9999?
```

**Očekávaný výsledek:** Agent odpoví že objednávku nenašel, požádá zákazníka o ověření čísla.

---

## T08 — Spam / nesouvisející e-mail

**Předmět:** Spolupráce — nabídka reklamy
**Tělo:**

```
Dobrý den, nabízíme reklamní plochy na fitness portálech. Máte zájem o spolupráci?
```

**Očekávaný výsledek:** Agent klasifikuje jako `unknown`, nereaguje zákazníkovi, pouze zaloguje.

---

## Jak vyhodnotit výsledky

Po každém testu zaznamenat:

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
