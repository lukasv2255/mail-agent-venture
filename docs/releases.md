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

## v1 — [datum první nasazení]

**Template commit:** `9b791f0`
**Nasazeno:** Railway

Počáteční nasazení. Sorter, základní dashboard, Telegram approval flow.

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
