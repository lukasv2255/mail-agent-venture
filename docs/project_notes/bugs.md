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

## Příklady

## 2026-03-29 — DB připojení selhává na stagingu

**Symptom:** `Connection refused` při spuštění app na stagingu

**Root cause:** Staging používá port `5433`, ne výchozí `5432`

**Řešení:** Aktualizovat `DATABASE_URL` v `.env.staging` na správný port

**Prevence:** Viz `key_facts.md` — staging DB port je vždy `5433`

---
