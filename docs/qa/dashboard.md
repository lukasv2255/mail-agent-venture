# Dashboard — Visual QA

Každá změna dashboardu musí projít těmito kontrolami přes Playwright. Dělej je sám, nečekej na pokyn.

1. **Refresh persistence** — reload → všechna tlačítka a texty musí být stejné
2. **Prázdný stav** — 30s bez emailu → karta nesmí být prázdná ani blikat
3. **Polling flicker** — screenshot každé 2s po dobu 10s → žádné probliknutí
4. **Side effects** — po kliknutí zkontroluj logy (Telegram unpin, DB záznam...)

Hledej aktivně: probliknutí stavů, emoji/text jen v JS (zmizí po refreshi), akce bez backend callu, chybějící fallback při prázdných datech.
