# Lessons — Naučené poučení

> Claude: přečti tento soubor na začátku každé session.
> Po každé korekci nebo chybě přidej poučení sem.

---

## 2026-04-16 — Nikdy nepřepisovat .env bez kontroly

**Situace:** Uživatel řekl "vytvoř .env", soubor už existoval a byl vyplněný. Claude ho přepsal.

**Chyba:** Použil Write bez předchozího ověření existence souboru.

**Správně:** Před vytvořením `.env` vždy zkontrolovat `ls` nebo `Glob` jestli soubor existuje. Pokud ano, vypsat obsah a zeptat se jestli přepsat.

**Pravidlo:** `.env` nelze obnovit z gitu — přepsání = ztráta dat.

---

## 2026-04-16 — Telegram handler nesmí blokovat event loop

**Situace:** `/yes` nereagoval — agent čekal na Future ale handlery se nespustily.

**Chyba:** `await run_check()` přímo v handleru blokuje celý event loop dokud check neskončí.

**Správně:** `asyncio.create_task(run_check())` — check běží na pozadí, handlery fungují normálně.

**Pravidlo:** Jakákoliv dlouho běžící async operace v Telegram handleru = `create_task`, ne `await`.

---

## Obecné principy práce s Tommym

- Tommy se **učí**, nejen kopíruje — vždy vysvětli proč, nejen co
- Preferuje **jedno správné řešení** před výběrem z pěti možností
- Rychle pochopí koncepty — nemusíš vysvětlovat základy Pythonu
- Cílí na **nasazené, prezentovatelné projekty** — vyhni se over-engineeringu
- Komunikace česky

## 2026-03-30 — Testovat sám, nežádat uživatele

**Situace:** Po každé drobné úpravě kódu Claude žádal Tommyho aby otestoval sám.

**Chyba:** Přehazování zodpovědnosti za testování na uživatele.

**Správně:** Po drobné úpravě napsat "Testuji přidání X..." a spustit test sám. Reportovat výsledek.

**Pravidlo:** Drobné změny vždy otestuj sám a reportuj výsledek — nereferuj uživatele.

---

## 2026-04-13 — Šablony ukotvovat do projektové memory

**Situace:** Vznikal obecný podklad pro support use-cases, ale uživatel upřesnil,
že výstup má sloužit jako šablona přímo pro tento projekt a jeho další mail agenty.

**Chyba:** Příliš obecný dokument bez pevného napojení na `CLAUDE.md`,
`docs/project_notes/` a `tasks/`.

**Správně:** Když se staví reusable template, ukotvit ji do existující projektové
struktury, decisions a key facts, ne jen do samostatného dokumentu.

**Pravidlo:** Obecný návrh vždy převeď do místní projektové memory a repové šablony.

---

## 2026-04-16 — Správný formát testovacího emailu přes Gmail API

**Situace:** Testovací email dorazil bez subject — agent klasifikoval jako `unknown` a přeskočil.

**Chyba:** Nastaven `msg['from']` header — Gmail ho přepisuje a při tom rozhází ostatní headery, subject se ztratí.

**Správně:**

```python
msg = MIMEText('tělo', 'plain', 'utf-8')
msg['to'] = 'newagent7878@gmail.com'
msg['subject'] = 'Předmět'
# NENASTAVUJ msg['from'] — Gmail ho přepíše a ztratí se subject
raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
service.users().messages().send(userId='me', body={'raw': raw}).execute()
```

**Pravidlo:** Používej `EmailMessage` (ne `MIMEText`) — `MIMEText` generuje lowercase `subject:` header který Gmail ignoruje → subject se ztratí.

```python
from email.message import EmailMessage
msg = EmailMessage()
msg['To'] = 'newagent7878@gmail.com'
msg['Subject'] = 'Předmět'
msg.set_content('Tělo emailu')
raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
service.users().messages().send(userId='me', body={'raw': raw}).execute()
```

---

## 2026-04-17 — Dashboard: ESC/UNK dismiss odepíná Telegram, polling bez probliknutí

**Situace:** Dashboard zobrazoval probliknutí "📭" mezi zpracováním emailů, ESC/UNK neodpínalo Telegram, a stav "žádný email" byl matoucí.

**Řešení:**

- **ESC/UNK dismiss → unpin Telegram:** `message_id` se ukládá do alertu při vzniku, tlačítko "Vyřízeno" volá unpin callback přes `message_id`. Pattern: alert obsahuje `telegram_message_id`.
- **\_isPolling flag:** Zabrání přepsání karty na "📭" v mezeře mezi HTTP polling cykly — flag se nastaví před fetchem, odstraní po dokončení celého cyklu.
- **Vždy "⏳ Čekám na další email...":** Odstraněn stav "📭 Žádný email nečeká" — agent běží ve smyčce pořád, takže karta vždy ukazuje čekání.
- **Tlačítko "🔍 Check now":** Lupa je v HTML i JS takže přežije každý refresh.

**Pravidlo:** Emoji v tlačítkách a stavových kartách vždy definuj v HTML i v JS renderovací logice — jinak se po refresh ztratí.

---

## Šablona záznamu

```markdown
## [Datum] — [Název poučení]

**Situace:** Co se stalo

**Chyba:** Co bylo špatně nebo co nefungovalo

**Správně:** Jak to dělat příště

**Pravidlo:** [Jednořádkové shrnutí]
```

---
