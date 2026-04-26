# Lessons — Naučené poučení

> Claude: přečti tento soubor na začátku každé session.
> Po každé korekci nebo chybě přidej poučení sem.

---

## 2026-04-21 — Více procesů = více newsletterů

**Situace:** Přišly 4 newslettery místo jednoho. Agent běžel přes launchd (KeepAlive: true) a zároveň byl ručně spuštěn `python3 main.py`. Každý proces má vlastní job queue → každý odešle newsletter samostatně.

**Chyba:** Spuštění `python3 main.py` ručně zatímco launchd již běží → dvě instance, 409 Conflict od Telegramu, duplicitní newslettery/zprávy.

**Správně:** Pokud běží launchd, ovládat agenta pouze přes `launchctl start/stop/kickstart`. Nikdy `python3 main.py` ručně.

**Pravidlo:** Počet odeslaných newsletterů = počet běžících instancí agenta. Vždy zkontrolovat: `ps aux | grep "main.py" | grep -v grep`

---

## 2026-04-25 — Sorter feedback musí mít vlastní persistentní storage

**Situace:** Dashboard dostal ruční akci `Přesunout do spamu` pro dříve ponechaný email a uživatel chtěl, aby si to agent pamatoval i po redeploy.

**Chyba:** Spoléhat na `logs/sorter/sorter.jsonl` nestačí. Historie slouží hlavně jako audit a lokální soubory na Railway bez persistentního volume po redeploy zmizí.

**Správně:** Ruční pravidla ukládat odděleně od historie, ideálně do `DATA_DIR/sorter_rules.db`, a sorter je aplikovat před AI klasifikací. Dashboard akce musí uložit pravidlo i přesunout konkrétní email.

**Pravidlo:** Audit log není persistentní pravidlové úložiště. Cokoliv se má "naučit" pro příště, patří do samostatné storage.

---

## 2026-04-20 — Soubeh sorteru a responderu vyžaduje časové okno

**Situace:** Sorter a responder mohou běžet nad stejným IMAP inboxem, pokud má sorter čas email roztřídit dřív, než ho začne řešit responder. V produkčním režimu s `AUTO_RESPOND=true` email typicky několik minut sedí ve schránce a sorter ho v řádu sekund až jedné minuty odklidí nebo ponechá.

**Chyba:** Absolutní pravidlo "sorter a responder nikdy spolu" je příliš silné. Skutečné riziko je krátké nebo nulové časové okno: ruční `/check`, startovní check po restartu, příliš krátký `CHECK_INTERVAL_MINUTES`, nebo testovací běh, kde responder začne zpracovávat inbox dřív, než sorter dokončí třídění.

**Správně:** V běžném provozu mohou být `MODULE_SORTER=true` a `MODULE_RESPONDER=true` současně, pokud je responder plánovaný tak, aby maily nebral okamžitě a sorter měl náskok. Pro čistý izolovaný test konkrétního modulu ale pořád vypínej druhý modul: při testování sorteru `MODULE_RESPONDER=false`, při testování responderu `MODULE_SORTER=false`.

**Pravidlo:** Soubeh sorteru a responderu je bezpečný jen s dostatečným časovým oknem pro sorter; nevyvozuj z testu spuštěného hned po restartu závěr, že produkční souběh je špatně.

---

## 2026-04-18 — Railway `variable list` zkracuje hodnoty — nepoužívat pro kopírování tokenů

**Situace:** Při kopírování env proměnných z Railway CLI (`railway variable list`) do nového projektu byl TELEGRAM_BOT_TOKEN zkrácen v zobrazení → token byl neplatný → app spadla.

**Chyba:** Hodnoty zkopírované z `railway variable list` výstupu mohou být oříznuté. Tokeny a API klíče se pak nastaví nesprávně.

**Správně:** Citlivé hodnoty (tokeny, API klíče) vždy brát ze zdrojového `.env` souboru nebo přímo od uživatele — nikdy z `railway variable list` výstupu.

**Pravidlo:** `railway variable list` je jen pro přehled, ne pro kopírování hodnot.

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

## 2026-04-22 — Trigger fráze pro ukládání paměti

**Situace:** Uživatel chce používat krátké fráze jako příkaz k trvalému zapsání pravidel a poznatků.

**Správně:** Frázi `nauč se` ber jako pokyn uložit poznatek do projektového nebo lokálního `.md` souboru podle kontextu. Frázi `dokumentuj` ber jako pokyn zapsat informaci do aktuální projektové paměti, typicky `tasks/lessons.md`, `docs/bugs.md`, nebo jiného relevantního memory dokumentu. Frázi `run` ber jako pokyn spustit projekt konkrétní cestou přes launchd; hlavního agenta nepouštěj ručně přes `python3 main.py`.

**Pravidlo:** `nauč se` = uložit do projektového/lokálního MD; `dokumentuj` = zapsat do lessons/bugs/memory aktuálního projektu; `run` = spustit projekt přes launchd.

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
msg['to'] = os.getenv('TEST_TARGET_EMAIL', os.getenv('GMAIL_ADDRESS', ''))
msg['subject'] = 'Předmět'
# NENASTAVUJ msg['from'] — Gmail ho přepíše a ztratí se subject
raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
service.users().messages().send(userId='me', body={'raw': raw}).execute()
```

**Pravidlo:** Používej `EmailMessage` (ne `MIMEText`) — `MIMEText` generuje lowercase `subject:` header který Gmail ignoruje → subject se ztratí.

```python
from email.message import EmailMessage
msg = EmailMessage()
msg['To'] = os.getenv('TEST_TARGET_EMAIL', os.getenv('GMAIL_ADDRESS', ''))
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
