# Todo — Aktuální úkoly

> Claude: sem zapisuj plán před každou netriviální implementací.
> Označuj hotové položky. Po dokončení přidej sekci "Výsledky".

---

## Šablona

```markdown
## [Datum] — [Název úkolu]

### Plán

- [ ] Krok 1
- [ ] Krok 2
- [ ] Krok 3

### Výsledky

[Co bylo skutečně uděláno, co se lišilo od plánu]
```

---

## 2026-04-13 — Mapování support email use-cases

### Plán

- [x] Zmapovat hlavní typy mailových systémů a support workflow
- [x] Převést zjištění do univerzální šablony zadání pro budoucí projekty
- [x] Uložit strukturovaný podklad do dokumentace repa

### Výsledky

Vytvořen podkladový dokument pro návrh email/support agentů v různých typech firem.
Obsahuje kategorizaci systémů, typické support agendy, rozdíly podle velikosti firmy
a návrh datového modelu pro interní znalostní/informační systém.

## 2026-04-13 — Převod repa na šablonu pro více mail agentů

### Plán

- [x] Navázat šablonu na lokální `CLAUDE.md` a projektovou memory strukturu
- [x] Popsat pevné části repa a proměnné části pro různé varianty agentů
- [x] Doplnit dokumentaci tak, aby z ní šly odvozovat další mail agent projekty

### Výsledky

Dokumentace repa byla rozšířena z obecného support mapování na konkrétní
projektovou šablonu pro rodinu mail agentů. Doplněny byly architektonické zásady,
template blueprint a aktuální stav projektu v projektové memory.

## 2026-04-16 — Náhodné zpoždění odeslání odpovědi

### Plán

- [ ] Před odesláním odpovědi počkat náhodný čas (např. 2–8 minut)
- [ ] Zpoždění logovat, aby bylo jasné že email čeká na odeslání

### Kontext

Okamžitá odpověď vypadá strojově. Náhodné zpoždění simuluje lidského operátora.

---

## 2026-04-16 — Timeout bez upozornění (Komplikace č. 1)

### Plán

- [ ] Po 4 minutách poslat Telegram připomenutí: "⏰ Čeká na schválení — ještě 1 minuta."
- [ ] Po timeoutu poslat: "⚠️ Vypršel čas. Email přeskočen — odpověz zákazníkovi ručně."
- [ ] Zvážit prodloužení timeoutu z 5 na 15 minut

### Kontext

Aktuálně: timeout → tiché přeskočení, zákazník nedostane odpověď, klient nedostane žádné upozornění. Email označen jako zpracovaný = agent ho už nezpracuje znovu.

---

## 2026-04-16 — Duplicitní zpracování follow-up emailů (Komplikace č. 2)

### Plán

- [ ] Implementovat thread_id deduplikaci — pokud vlákno už bylo zodpovězeno, přeskočit

### Kontext

Zákazník napíše 2 emaily ke stejné věci → agent sestaví 2 drafty najednou → klient dostane 2 Telegram notifikace.

---

## 2026-04-16 — ESC bez Telegram notifikace (Komplikace č. 3)

### Plán

- [ ] Pro ESC/UNK s eskalačními klíčovými slovy (reklamace, poškozený, nepřijatelné...) vždy poslat Telegram upozornění
- [ ] Upozornění: "⚠ Eskalace: reklamace od jan@email.cz — vyžaduje ruční odpověď."

### Kontext

Aktuálně: ESC email se označí jako zpracovaný, ale klient nedostane žádnou notifikaci → zákazník čeká 3 dny bez odpovědi.

---

## 2026-04-20 — Periodická kontrola nesprávně označených emailů

### Plán

- [ ] Jednou za X hodin projít všechny emaily ve složce `others` (SEEN) a ověřit zda nebyly omylem přesunuty/označeny
- [ ] Emaily které vypadají jako zákaznické dotazy (ne B2B/spam) reportovat jako ESC do Telegramu
- [ ] Nabídnout odeslání odpovědi: "⚠ Tento email mohl být přeskočen omylem. Chceš odpovědět?"

### Kontext

Sorter může omylem označit jako SEEN nebo přesunout zákaznický email (např. reklamaci).
Zákazník pak čeká bez odpovědi. Periodická kontrola je záchranná síť.

---

## 2026-04-16 — Sekvenční fronta schválení (Komplikace č. 4)

### Plán

- [ ] Přepsat approval flow tak aby neprocesovalo emaily sekvenčně
- [ ] Drafty posílat do Telegramu s ID (/yes 1, /yes 2...) nebo přes inline tlačítka
- [ ] Schválení řešit nezávisle na smyčce emailů

### Kontext

Aktuálně: `for email in emails: await process_email(...)` — každý email blokuje dokud nepřijde /yes nebo /no (timeout 5 min). Pro 5 emailů = až 25 min blokování.
Přijatelné pro testování. Opravit před produkcí s vyšším objemem emailů.
