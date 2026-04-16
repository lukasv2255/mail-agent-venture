---
name: refactor
description: Řízený refactoring kódu. Použij když uživatel chce zlepšit strukturu, snížit komplexitu, nebo odstranit tech debt. NEPOUŽÍVEJ pro jednoduché opravy.
allowed-tools: Read, Grep, Glob, Edit, Write
---

# Refactoring Playbook

## Před refactoringem

1. Přečti a pochop stávající kód
2. Ověř, že existují testy (nebo je napiš)
3. Identifikuj konkrétní problémy — nerefaktoruj "jen tak"

## Principy

- **Malé kroky:** jeden refactor najednou, ne celý soubor naráz
- **Zelené testy:** testy musí projít před i po každém kroku
- **Zachovej chování:** refactoring nesmí měnit funkcionalitu
- **Ptej se:** "Je toto elegantnější řešení? Proč?"

## Časté vzory k opravení

- Dlouhé funkce (>50 řádků) → rozděl na menší
- Hluboko zanořené podmínky → early return / guard clauses
- Duplicitní kód → extrahuj helper
- Magic numbers → pojmenované konstanty
- God objects → rozděl zodpovědnosti

## Výstup

Po každém kroku popiš: co jsi změnil a proč. Spusť testy.
