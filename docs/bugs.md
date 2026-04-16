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

## 2026-04-16 — Gmail token vyprší mezi sezeními

**Symptom:** Agent při spuštění selže na Gmail API — token je neplatný nebo vypršel.

**Root cause:** `token.json` obsahuje access_token (platný 1 hod) a refresh_token. Refresh token vyprší pokud je Google OAuth app ve stavu "Testing" a nepoužívá se 7 dní — Google ho automaticky zneplatní.

**Řešení:** Znovu spustit OAuth flow: smazat `token.json` a spustit `gmail_client.py` lokálně — otevře prohlížeč pro nové přihlášení.

**Prevence:**

- Přidat Google OAuth app do stavu "Production" (nevyžaduje review pro osobní účty)
- Nebo přidat validaci tokenu při startu agenta s automatickým refresh pokusem

---

## Příklady

## 2026-03-29 — DB připojení selhává na stagingu

**Symptom:** `Connection refused` při spuštění app na stagingu

**Root cause:** Staging používá port `5433`, ne výchozí `5432`

**Řešení:** Aktualizovat `DATABASE_URL` v `.env.staging` na správný port

**Prevence:** Viz `key_facts.md` — staging DB port je vždy `5433`

---
