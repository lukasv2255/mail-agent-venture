# Test: Email body display na dashboardu

## Problem

V sorter historii na dashboardu se tělo emailu zobrazovalo jako `—` (pomlčka)
místo čitelného textu.

## Root cause

Tři příčiny dohromady:

**1. `_extract_body()` v `sorter.py` neměl HTML fallback**

Funkce hledala pouze `text/plain` část. HTML-only emaily (bez plain text části)
vrátily `""`. Starý kód:

```python
def _extract_body(msg) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":  # <-- jen plain text
                payload = part.get_payload(decode=True)
                if payload:
                    return payload.decode("utf-8", errors="replace")
    payload = msg.get_payload(decode=True)
    if payload:
        return payload.decode("utf-8", errors="replace")
    return ""  # <-- HTML-only emaily skončily zde
```

**2. Emaily třízené přes hlavičky nebo pravidla se logovaly s `body=""`**

`_log_sort()` dostával prázdný body string pro emaily klasifikované bez
extrakce textu (newsletterové hlavičky, naučená pravidla, vlastní emaily).

**3. JSONL záznam neměl pole `body_display`**

Frontend četl `item.body` přímo z JSONL. Pole chybělo nebo bylo prázdné
pro výše zmíněné případy.

## Oprava

- `sorter.py` — `_extract_body()` rozšířen o HTML fallback s odstraněním tagů:
  ```python
  for part in msg.walk():
      if part.get_content_type() == "text/html":
          html = payload.decode(...)
          return re.sub(r"<[^>]+>", " ", html).strip()
  ```
- `sorter.py` — `_log_sort()` zapisuje `body_display: body[:1000]` do JSONL
- `dashboard.html` — frontend čte `item.body_display || item.body || "—"`
- `dashboard.html` — vyřešen merge konflikt (ours/theirs v sorter detail bloku)

## Testovací skript

```bash
python3 tests/email_body/send_html_body_test.py
```

Odešle 3 emaily:

| #   | Typ                    | Předmět                                 | Starý kód | Nový kód     |
| --- | ---------------------- | --------------------------------------- | --------- | ------------ |
| 1   | HTML-only              | `[TEST body-display] HTML-only email…`  | `—`       | čitelný text |
| 2   | Multipart (plain+HTML) | `[TEST body-display] Multipart email…`  | OK        | OK           |
| 3   | Plain text             | `[TEST body-display] Plain text email…` | OK        | OK           |

## Jak ověřit

1. Spusť skript — odešle 3 emaily na inbox agenta
2. Počkej až sorter emaily zpracuje
3. Dashboard → Sorter sekce → rozklikni každý `[TEST body-display]` řádek
4. **Očekávaný výsledek:** všechny 3 zobrazí čitelný text
5. **Selhání:** HTML-only email zobrazuje `—` nebo raw HTML tagy (`<p>`, `<br>`)
