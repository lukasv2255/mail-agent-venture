# Releases — mail-agent-venture

Přehled verzí nasazených na tuto klientskou instanci.
Šablona: `github.com/lukasv2255/mail-agent`

---

## v2 — 2026-04-26

**Template commit:** `81def9c`
**Nasazeno:** Railway

### Co je nového

- **Sorter rules persistence** — ruční korekce z dashboardu (Přesunout do spamu) se ukládají do `DATA_DIR/sorter_rules.db` jako trvalá pravidla
- **Sorter před AI** — uložená pravidla se aplikují dřív než OpenAI klasifikace
- **Dashboard: sorter feedback** — zobrazení aktivních pravidel, tlačítko pro ruční korekci
- **config.py: DATA_DIR** — všechna runtime data jdou přes `DATA_DIR`, připraveno na Railway volume
- **railway_deploy.md** — nová dokumentace doporučeného deploy workflow
- **Reorganizace tests/** — plochá struktura, nové testovací sady (sorter_state, data_persistence, email_body)

### Infrastruktura — manuální kroky po deployi

- [ ] Railway dashboard → service → **Volumes → Add Volume → Mount Path: `/data`**
- [ ] `railway variables set DATA_DIR=/data`
- [ ] Nový deploy: `railway up --detach --message "v2: sorter persistence + Railway volume"`

### Soubory změněné oproti v1

| Soubor                              | Změna                               |
| ----------------------------------- | ----------------------------------- |
| `main.py`                           | minor úpravy orchestrace            |
| `src/config.py`                     | DATA_DIR jako centrální cesta       |
| `src/dashboard.py`                  | sorter feedback endpoints           |
| `src/gmail_client.py`               | drobné opravy                       |
| `src/modules/sorter.py`             | rules engine, persistence           |
| `src/sorter_rules.py`               | **nový** — SQLite CRUD pro pravidla |
| `templates/dashboard.html`          | sorter sekce, feedback UI           |
| `scripts/client_instance_wizard.py` | aktualizace wizard                  |
| `docs/railway_deploy.md`            | **nový** — deploy checklist         |

---

## v2.1 — 2026-04-26

**Commits:** `c509184`, `19129c5`
**Nasazeno:** Railway

- dashboard: nadpis přejmenován na "Mail agent Venture"
- sorter: oprava chybějícího `import re` v `_extract_body`

---

## v1 — 2026-04-22

**Template commit:** `e65357b`
**Nasazeno:** Railway

Počáteční nasazení. Projekt převeden na reusable template šablonu.

### Historie vývoje (před Railway nasazením)

| Datum      | Commit    | Co přibylo                                                    |
| ---------- | --------- | ------------------------------------------------------------- |
| 2026-03-30 | `3a87183` | Initial commit — Gmail API, GPT-4o mini, Telegram notifikace  |
| 2026-04-13 | `aee1b1d` | Znalostní báze, projektová šablona, mail klienti              |
| 2026-04-15 | `962071d` | KB, učení agenta, shadow mode                                 |
| 2026-04-16 | `cc79757` | Mail client abstrakce, kb_loader, async /yes flow             |
| 2026-04-16 | `4e367c0` | Klasifikace A1-B2/ESC/UNK, response prompty                   |
| 2026-04-17 | `605c4dc` | Dashboard unpin Telegram on dismiss, UI polish                |
| 2026-04-18 | `8123620` | Newsletter modul — real estate leads Morava                   |
| 2026-04-20 | `b4e55ca` | IMAP UID tracking, asyncio loop, ESC/UNK složky, multi-folder |
| 2026-04-20 | `5aa6707` | Reorganizace tests/, README dokumentace                       |
| 2026-04-22 | `566afbf` | Railway web port pro dashboard                                |
| 2026-04-23 | `9b791f0` | Client setup wizards                                          |

---

## Jak přidávat nový release

```
## vN — YYYY-MM-DD

**Template commit:** `<git sha>`
**Nasazeno:** Railway / launchd

### Co je nového
- ...

### Infrastruktura — manuální kroky po deployi
- [ ] ...

### Soubory změněné oproti vN-1
| Soubor | Změna |
```
