---
# Bez paths = načítá se vždy
---

# Pravidla pro testy

- Piš testy **před** nebo **zároveň** s implementací (ne po)
- Každá nová funkce nebo fix musí mít odpovídající test
- Testy pojmenovávej: `should [expected behavior] when [condition]`

## Co testovat

- Happy path (úspěšný případ)
- Edge cases (prázdné vstupy, nulové hodnoty, hraniční hodnoty)
- Error handling (co se stane při chybě)

## Co netestovat

- Interní implementační detaily
- Frameworkové funkce (React hooks samy o sobě)

## Databáze v testech

- Testy používají **reálnou lokální DB**, ne mocky
- Před spuštěním: `npm run db:test:reset`
- Každý test musí po sobě uklidit data

## Pokrytí

- Kritické moduly (auth, platby): min. 80% coverage
- Ostatní: rozumné pokrytí, ne za každou cenu 100%
