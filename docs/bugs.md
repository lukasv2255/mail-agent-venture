# Bugs — Vyřešené problémy

> Claude: před debugováním zkontroluj tento soubor. Stejný bug mohl být vyřešen dříve.
> Po vyřešení nového bugu přidej záznam sem.

---

## Šablona záznamu

```markdown
## [Datum] — [Stručný název bugu]

**Symptom:** Co se dělo (error message, nesprávné chování)

**Root cause:** Proč to nastalo

**Řešení:** Co bylo opraveno

**Prevence:** Jak se tomu vyhnout příště
```

---

## 2026-04-16 — /yes a /no nereagují po /check

**Symptom:** Agent pošle návrh odpovědi do Telegramu a čeká na `/yes`, ale příkaz je ignorován.

**Root cause:** `run_check()` bylo voláno jako `await` přímo v handleru — blokovalo event loop. `wait_for_approval()` drželo coroutine, ale Telegram handlery (`cmd_yes`, `cmd_no`) se nemohly spustit dokud `run_check` neskončil.

**Řešení:** Spustit check jako background task:

```python
# bylo:
await run_check(context.bot)
# opraveno na:
asyncio.create_task(run_check(context.bot))
```

**Prevence:** Každá dlouho běžící operace spuštěná z Telegram handleru musí být `create_task` — jinak Telegram přestane reagovat na příkazy.

---

## 2026-04-20 — \_extract_body crashuje na emailech bez plain text payloadu

**Symptom:** `AttributeError: 'NoneType' object has no attribute 'decode'` v `mail_client_imap.py` — agent se zasekne a přestane zpracovávat emaily.

**Root cause:** `msg.get_payload(decode=True)` vrátí `None` pro multipart emaily bez plain text části (např. HTML-only emaily, automatické odpovědi). Volání `.decode()` na `None` spadne.

**Řešení:** Ověřit `payload` před `.decode()`:

```python
payload = msg.get_payload(decode=True)
if payload:
    return payload.decode("utf-8", errors="replace")
return ""
```

**Prevence:** Vždy kontrolovat návratovou hodnotu `get_payload(decode=True)` — může být `None`.

---

## 2026-04-20 — Soubeh sorteru a responderu bez časového okna koliduje

**Symptom:** Při testu spuštěném hned po restartu nebo přes ruční `/check` může responder zpracovat emaily dřív, než sorter dokončí třídění. V minulosti se to projevovalo i tím, že po sorter fetchi responder některé emaily nenašel.

**Root cause:** Problém není samotný souběh modulů, ale absence dostatečného časového okna. Sorter pracuje v řádu sekund až jedné minuty, zatímco responder může při startovním/scheduled/ručním checku okamžitě sáhnout do stejného inboxu.

**Řešení:** V produkčním režimu mohou sorter a responder běžet současně, pokud responder nechává emaily několik minut ve schránce a sorter má náskok. Pro izolované testy vypnout netestovaný modul.

**Prevence:** Nevyhodnocovat produkční souběh podle testu spuštěného hned po restartu. Při společném běhu hlídat `CHECK_INTERVAL_MINUTES`, startovní check a ruční `/check`, aby responder nepředběhl sorter.

---

## 2026-04-16 — Gmail token vyprší mezi sezeními

**Symptom:** Agent při spuštění selže na Gmail API — token je neplatný nebo vypršel.

**Root cause:** `token.json` obsahuje access_token (platný 1 hod) a refresh_token. Refresh token vyprší pokud je Google OAuth app ve stavu "Testing" a nepoužívá se 7 dní — Google ho automaticky zneplatní.

**Řešení:** Znovu spustit OAuth flow: smazat `token.json` a spustit `gmail_client.py` lokálně — otevře prohlížeč pro nové přihlášení.

**Prevence:**

- Přidat Google OAuth app do stavu "Production" (nevyžaduje review pro osobní účty)
- Nebo přidat validaci tokenu při startu agenta s automatickým refresh pokusem

---

## 2026-04-20 — COPY BAD: Bad MSN — 3 emaily zůstávají v inboxu

**Symptom:** Po zpracování prvních emailů selže `mark_as_processed` s `COPY command error: BAD: Bad MSN (message sequence number)`. Zbývající emaily zůstanou v inboxu nezpracované.

**Root cause:** `email_id` bylo IMAP **MSN (message sequence number)** — pořadové číslo v inboxu. Po smazání emailu č. 1 se přečíslují všechny následující (původní MSN 2 se stane MSN 1 atd.). Uložená MSN pak odkazuje na jiný nebo neexistující email.

**Řešení:** Přepnout na **UID** (`conn.uid("SEARCH", ...)`, `conn.uid("FETCH", ...)`, `conn.uid("COPY", ...)`, `conn.uid("STORE", ...)`). UID jsou trvalé — nezmění se při mazání jiných zpráv.

**Prevence:** Vždy používat UID variantu IMAP příkazů při jakékoliv operaci která kombinuje fetch + delete více zpráv.

## 2026-04-20 — "Future attached to different loop" — /check se zasekne

**Symptom:** `/check` visí v Telegramu jako "Spouštím check emailů..." bez odezvy. V logu: `RuntimeError: Task got Future <Future pending> attached to a different loop`.

**Root cause:** Dva problémy zároveň:

1. `_check_lock = asyncio.Lock()` byl vytvořen na úrovni modulu (před spuštěním event loop). `app.run_polling()` vytvoří vlastní loop přes `asyncio.run()` → lock je vázán na jiný loop.
2. `set_check_callback` volal `asyncio.get_event_loop()` před startem `run_polling()` → `_main_loop` ukazoval na jiný loop než ten, kde bot běží.

**Řešení:**

- `_check_lock` se vytváří lazily při prvním volání `run_check()` (uvnitř správného loopu)
- `set_check_callback` se volá z `post_init` callbacku (python-telegram-bot v20 feature) — ten běží uvnitř správného loopu
- `asyncio.get_event_loop()` → `asyncio.get_running_loop()` v `set_check_callback`

**Prevence:** Nikdy nevytvářet `asyncio.Lock()` na úrovni modulu. `run_polling()` si vytváří vlastní event loop — vše co s ním interaguje musí být vytvořeno uvnitř `post_init` nebo async kontextu.

## 2026-04-25 — Tělo emailu se nezobrazuje v sorter historii na dashboardu

**Symptom:** V sorter historii (rozkliknutý řádek) se tělo emailu zobrazuje jako `—` nebo prázdné místo, přestože email tělo obsahoval.

**Root cause:** Tři příčiny dohromady:

1. `item.body` bylo v JSONL prázdné (`""`) pro emaily klasifikované přes hlavičky nebo naučená pravidla — `_log_sort()` jim předával `body=""` bez extrakce textu.
2. Pro HTML-only emaily vrací `_extract_body()` v `sorter.py` prázdný string — chybí HTML fallback (na rozdíl od `gmail_client.py` který ho má).
3. Gmail fallback vrátí surové HTML tagy — `esc()` v JS je escapuje, zobrazí se jako text se `&lt;p&gt;` apod.

**Řešení (částečné — netestováno):** Frontend změněn na `item.body_display || "—"` místo `item.body || "—"`. Pole `body_display` zatím v backendu neexistuje — bude potřeba přidat do `_log_sort()` v `sorter.py` jako čistý plain text (bez HTML tagů, zkrácený na rozumnou délku pro zobrazení).

**Stav:** Opraveno. Merge konflikt vyřešen. `body_display` přidáno do `_log_sort()`. HTML fallback opraven i v `gmail_client.py` (stejná příčina — vrací raw HTML tagy místo čistého textu). Netestováno na živém inboxu.

**Prevence:** Při logování sorter záznamu vždy extrahovat body před voláním `_log_sort()`, ne po. Přidat `body_display` do schématu záznamu hned při prvním zavedení sorter logování.

---

## Příklady

## 2026-03-29 — DB připojení selhává na stagingu

**Symptom:** `Connection refused` při spuštění app na stagingu

**Root cause:** Staging používá port `5433`, ne výchozí `5432`

**Řešení:** Aktualizovat `DATABASE_URL` v `.env.staging` na správný port

**Prevence:** Viz `key_facts.md` — staging DB port je vždy `5433`

---
