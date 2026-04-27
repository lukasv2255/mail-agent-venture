# Testování mail-agenta — průvodce pro Claude

Tento dokument popisuje jak správně projít celou testovací sadu. Je psán pro agenta (Claude), ne pro manuální testování.

## Předpoklady

- Agent běží na **Railway** (primární prostředí)
- Dashboard dostupný na `https://mail-agent-template-production.up.railway.app/`
- `.env` obsahuje `IMAP_USER` (inbox agenta, e.g. `johnybb11@seznam.cz`) a Gmail credentials
- Playwright MCP dostupný pro interakci s dashboardem

## Přehled testů

| Test                                              | Soubor                              | Typ            | Co ověřuje                                            |
| ------------------------------------------------- | ----------------------------------- | -------------- | ----------------------------------------------------- |
| [sorter_state](#1-sorter_state)                   | `sorter_state/test_sorter_state.py` | Unit (offline) | UID watermark — správné přeskakování starých emailů   |
| [email_body](#2-email_body)                       | `email_body/send_html_body_test.py` | Integration    | Body display v dashboardu pro HTML/plain/multipart    |
| [keep_rule_persistence](#3-keep_rule_persistence) | —                                   | Playwright     | Tlačítko "Vrátit a vždy ponechat" tvoří KEEP pravidlo |
| [rule_reapply](#4-rule_reapply)                   | `sorter/test_rule_reapply.py`       | Integration    | Pravidlo se zpětně aplikuje na dříve ponechané emaily |
| [sorter](#5-sorter)                               | `sorter/test_sorter.py`             | Integration    | AI třídí 30 emailů do správných kategorií             |

---

## Kritická pravidla PŘED spuštěním

### 1. Pravidla musí být čistá

Testy sdílejí odesílatele `newagent7878@gmail.com`. Pokud existuje KEEP nebo MOVE pravidlo pro tuto adresu, kazí výsledky dalších testů.

**Před každým testem ověř přes API:**

```javascript
// V Playwright evaluate:
fetch("/api/sorter/rules")
  .then((r) => r.json())
  .then((d) => console.log(d));
```

Pokud existují pravidla pro `newagent7878@gmail.com`, smaž je:

```javascript
fetch('/api/sorter/delete-rule-by-id', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({rule_id: <ID>})
})
```

### 2. `railway run` nepřistupuje k Volume

`railway run python3 ...` spustí nový container — **nemá přístup k `/data` volume** (sorter_rules.db, logy). Data čti výhradně přes HTTP API dashboardu nebo přes Playwright evaluate.

Správně:

```javascript
// Playwright evaluate
fetch("/api/sorter-history?page=1&per_page=50").then((r) => r.json());
fetch("/api/sorter/rules").then((r) => r.json());
```

Špatně:

```bash
railway run python3 -c "import sqlite3; ..."  # nezvidí /data volume
```

### 3. API endpoint pro sorter historii

Správný endpoint je `/api/sorter-history` (pomlčka), **ne** `/api/sorter/history` (lomítko).

---

## Postup testování

### 1. sorter_state

Offline unit testy, nevyžadují síť ani Gmail.

```bash
python3 tests/sorter_state/test_sorter_state.py
```

**Očekáváno:** `3 passed` (nebo ekvivalent bez chybového výstupu).

---

### 2. email_body

Pošle 4 testovací emaily, ověř body display v dashboardu přes Playwright.

```bash
python3 tests/email_body/send_html_body_test.py
```

Počkej až sorter zpracuje emaily (~30–120s), pak ověř přes Playwright:

- Otevři dashboard
- Najdi záznamy se subjektem `[TEST body-display]`
- Rozklikni každý a ověř: zobrazuje čitelný text (ne `—` ani raw HTML tagy)

**Poznámka:** Emaily budou přesunuty pravidlem pokud existuje MOVE pravidlo pro `newagent7878@gmail.com` — to nevadí, body display funguje i pro přesunuté emaily.

---

### 3. keep_rule_persistence

Ověřuje tlačítko "Vrátit a vždy ponechat" na dashboardu.

**Předpoklad:** V sorter historii musí existovat email s `outcome=moved` a `email_key` (přesunutý AI nebo pravidlem, bez existujícího pravidla — jinak se tlačítko nezobrazí).

**Kroky přes Playwright:**

1. Filtruj dashboard na "Přesunuto"
2. Najdi email s `outcome=moved` a bez `rule_type` (přesunutý AI)
3. Rozklikni řádek — musí být vidět tlačítko "Vrátit a vždy ponechat"
4. Klikni na tlačítko
5. Ověř status message: `"Email vrácen do inboxu a odesílatel přidán do KEEP pravidel."`
6. Ověř přes API: `fetch('/api/sorter/rules')` — musí obsahovat nové KEEP pravidlo

**Upozornění:** Po tomto testu existuje KEEP pravidlo pro `newagent7878@gmail.com`. **Smaž ho** před spuštěním `rule_reapply` nebo `sorter`.

---

### 4. rule_reapply

Ověřuje zpětné aplikování pravidla na dříve ponechané emaily.

**Předpoklad:** Žádné KEEP ani MOVE pravidlo pro `newagent7878@gmail.com`.

```bash
python3 tests/sorter/test_rule_reapply.py
```

**Kroky:**

1. Pošli emaily skriptem
2. Počkej až sorter zpracuje (AUTO mode) — ověř v dashboardu: 3× `[reapply-test]` jako Ponecháno
3. Rozklikni jeden z nich → klikni "Vždy od odesílatele"
4. Ověř status message: `"Email přesunut. Naučeno jako odesílatel."`
5. Ověř přes API: `fetch('/api/sorter/rules')` — musí existovat MOVE pravidlo
6. **Zpětná aplikace:** Pošli v Telegramu `/sort` — ostatní `[reapply-test]` emaily musí přejít na Přesunuto

**Omezení pro automatizaci:** Krok 6 (`/sort`) vyžaduje Telegram a nelze automatizovat. Ověř kroky 1–5, krok 6 označ jako "manuální".

**Jak ověřit status message přes Playwright bez čekání:**
Po kliknutí na tlačítko zkontroluj snapshot — status message je v elementu `e11` nebo podobném v patičce stránky.

---

### 5. sorter (30 emailů)

**Předpoklad:** Žádná pravidla pro `newagent7878@gmail.com` — jinak SPAM emaily budou nesprávně ponechány.

```bash
python3 tests/sorter/test_sorter.py
```

Počkej až sorter zpracuje všechny emaily (může trvat 2–5 minut v AUTO mode).

**Ověření přes Playwright evaluate:**

```javascript
async () => {
  let all = [];
  for (let p = 1; p <= 5; p++) {
    const d = await fetch(`/api/sorter-history?page=${p}&per_page=50`).then(
      (r) => r.json(),
    );
    all.push(...(d.items || []));
    if (p >= d.pages) break;
  }
  // Filtruj dnešní emaily bez prefixů [MIX/INQ/NWS/SPM]
  const today = new Date().toISOString().slice(0, 10);
  return all
    .filter((i) => i.time?.startsWith(today) && !/^\[/.test(i.subject || ""))
    .map((i) => ({
      subject: i.subject?.slice(0, 40),
      outcome: i.outcome,
      method: i.method,
    }));
};
```

**Očekávané výsledky:**

- 12 SPAM emailů (S01–S12) → `outcome: moved`
- 8 poptávek (P01–P08) → `outcome: kept`
- 10 newsletterů (N01–N10) → `outcome: moved`

**Tolerované odchylky:**

- Hraniční případy (S12 automatická odpověď, P04 nábytek) mohou jít jinam — AI není deterministická
- Emaily klasifikované `method: rule` místo `method: ai` jsou OK pokud `outcome` sedí

---

## Doporučené pořadí testů

```
1. sorter_state      — offline, vždy první
2. email_body        — nevyžaduje čistou DB
3. sorter            — čistá DB pravidel!
4. rule_reapply      — čistá DB pravidel!
5. keep_rule_persistence — vytváří pravidlo, spouštět jako poslední
```

---

## Časté problémy

| Symptom                                                         | Příčina                                                                 | Řešení                                             |
| --------------------------------------------------------------- | ----------------------------------------------------------------------- | -------------------------------------------------- |
| SPAM emaily klasifikované jako Ponecháno s `method: rule`       | Aktivní KEEP pravidlo pro `newagent7878@gmail.com`                      | Smaž pravidlo přes `/api/sorter/delete-rule-by-id` |
| Dashboard zobrazuje `kept` i po kliknutí "Vždy od odesílatele"  | Dedup v historii preferuje starší záznam — backend akci provedl správně | Důvěřuj status message na stránce, ne historii     |
| `/api/sorter/history` vrací 404                                 | Špatný endpoint                                                         | Správně: `/api/sorter-history` (pomlčka)           |
| `railway run python3 -c "...DB..."` nenajde data                | `railway run` nepřipojuje Volume                                        | Čti data přes HTTP API                             |
| 3. email `[reapply-test] Potvrzení objednávky` chybí v historii | Dedup — stejný semantic_key jako starší test run                        | Ignoruj, funkčnost potvrzena prvními dvěma emaily  |
