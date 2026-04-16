---
name: code-review
description: Detailní code review zaměřený na správnost, udržitelnost a výkon. Použij při review PR, kontrole implementace, nebo před mergem do main.
allowed-tools: Read, Grep, Glob
---

# Code Review Checklist

## Správnost
- [ ] Logika odpovídá požadavkům
- [ ] Edge cases jsou ošetřeny (null, undefined, prázdné pole)
- [ ] Error handling je přítomen a smysluplný
- [ ] Žádné race conditions nebo async chyby

## Architektura
- [ ] Kód dodržuje existující vzory v projektu
- [ ] Žádné duplicate logiky (DRY)
- [ ] Funkce dělají jednu věc (SRP)
- [ ] Závislosti jsou minimální a odůvodněné

## Výkon
- [ ] Žádné zbytečné re-rendery (React)
- [ ] N+1 dotazy do DB
- [ ] Velká data jsou stránkována nebo lazy-loadována

## Bezpečnost
- [ ] Vstupy jsou validovány
- [ ] Auth je zkontrolována
- [ ] Žádné citlivé data v logu

## Výstup

Pro každý problém: **soubor:řádek** + popis + navrhovaný fix.
Uveď také co je dobře napsáno.
