# Mail Agent — Roadmap a nápady na rozvoj

Zaznamenáno: 2026-04-27

Tento soubor slouží jako živý seznam nápadů jak projekt komplexně rozvinout —
od drobných rozšíření sorterové logiky až po větší architektonické kroky.

---

## Sorter

### 1. Více výstupních složek (ne jen "others")

Pravidla by mohla definovat cílovou složku — místo binárního KEEP/MOVE by bylo MOVE + složka.
Faktury do `invoices`, objednávky do `orders`, GitHub notifikace do `github`.

- DB schéma: přidat sloupec `target_folder` do `sorter_rules`

### 2. Prioritizace (urgency score)

GPT by vracelo i `score 1–5` — KEEP emaily s vysokou prioritou by šly přes Telegram notifikaci okamžitě.

- Vyžaduje změnu v classifier promptu a parsování odpovědi

### 3. Automatické předání responderu s hintem

Sorter detekuje typ emailu → předá responderu hint (např. "toto je faktura, odpověz potvrzením přijetí").
Teď fungují jako separátní moduly bez sdílení kontextu.

### 4. Pravidla na předmět / tělo (regex)

Teď umí sorter MOVE pravidlo jen pro přesnou emailovou adresu nebo SHA256 hash obsahu.
Regex pravidlo by znamenalo: "přesuň každý email, jehož předmět odpovídá tomuto vzoru."

Příklad: pravidlo `subject_pattern = \[GitHub\]` → automaticky přesune všechny GitHub notifikace,
aniž by musel přidat adresu každého repozitáře zvlášť. Nebo `Vaše objednávka` → vždy do složky `orders`.

Změna by byla v `sorter_rules.py` — přidat nový `rule_type` a v `match_move_rule()`
místo `==` zavolat `re.search(rule_value, subject)`.

### 5. Trénování na zpětné vazbě (few-shot learning)

Teď má GPT fixní systémový prompt (`prompts/sorter/classifier_prompt.txt`).
Každou korekcí z dashboardu (klikneš "přesunout" na email co GPT ponechalo) vznikne signál:
_tento konkrétní email byl špatně klasifikován_.

Nápad: tyto korekce ukládat jako příklady do souboru (`data/sorter/feedback.jsonl`),
a při každém spuštění agenta přidat posledních 10–20 korekcí do promptu jako few-shot příklady:

```
Příklady minulých korekcí:
Od: newsletter@heureka.cz, Předmět: Slevy tohoto týdne → MOVE  ← byl chybně KEEP
Od: jan.novak@firma.cz, Předmět: Nabídka spolupráce → KEEP  ← byl chybně MOVE
```

GPT pak klasifikuje lépe bez toho, aniž bys musel měnit prompt ručně.
Systém se postupně "naučí" tvoje preference.

### 6. Statistiky a reporting

Data v `sorter.jsonl` jsou bohatá. Denní/týdenní přehled kolik emailů přišlo, od koho, kolik prošlo AI.

- Telegram příkaz `/stats`
- Dashboard widget

### 7. Whitelist domén (B2B kontext)

KEEP pravidlo pro celou doménu (`@firma.cz`), ne jen konkrétní adresu.

- `rule_type=domain`, `rule_value=firma.cz`

### 8. Zpracování příloh

Sorter vidí celý email — detekovat PDF přílohy a routovat je.
Faktury do účetního systému, smlouvy ke schválení.

- Vyžaduje parsing `multipart/mixed` a extrakci příloh

---

## Prioritní kandidáti pro implementaci

- **#4 (regex pravidla)** — rozšíření stávající rule engine, bez nových závislostí, malá změna
- **#1 (více složek)** — minimální změna DB, velký praktický dopad pro klientské instance
- **#5 (few-shot feedback)** — zvýší přesnost AI bez manuální práce, data už existují v dashboardu
