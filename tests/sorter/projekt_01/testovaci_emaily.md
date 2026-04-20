# Testovací e-maily — Sorter / Projekt 01 (E-shop s doplňky stravy)

Odesílatel: `newagent7878@gmail.com` → Příjemce: `johnybb11@seznam.cz`
Skript: `scripts/send_venture_test_emails.py`

Očekávaná klasifikace: `KEEP` (ponechat v inboxu) nebo `MOVE` (přesunout do `others`).

---

## MOVE — Spam a hromadné emaily

### T01 — SEO spam

**Předmět:** Váš web potřebuje SEO — zaručujeme 1. stránku Google
**Tělo:** Analyzovali jsme váš web a zjistili vážné problémy. Naše SEO služba zaručuje výsledky do 30 dní. Cena: 2 900 Kč/měsíc.
**Očekávaná klasifikace:** `MOVE` — hromadná marketingová nabídka

---

### T02 — Social media spam

**Předmět:** Získejte 10 000 nových sledujících na Instagramu za týden!
**Tělo:** Nabízíme garantovaný růst followerů na sociálních sítích. Výsledky do 7 dní nebo vrácení peněz.
**Očekávaná klasifikace:** `MOVE` — spam

---

### T03 — Faktura

**Předmět:** Faktura č. 2025-0342 — splatnost 30. dubna
**Tělo:** V příloze zasíláme fakturu č. 2025-0342 za měsíc březen.
**Očekávaná klasifikace:** `MOVE` — automatická systémová zpráva

---

### T04 — Automatická odpověď OOO

**Předmět:** Automatická odpověď: Jsem mimo kancelář
**Tělo:** Jsem momentálně mimo kancelář do 25. dubna. Naléhavé věci řeší kolega Jan Novák.
**Očekávaná klasifikace:** `MOVE` — automatická odpověď

---

### T05 — Newsletter

**Předmět:** Newsletter: Novinky z oboru — duben 2025
**Tělo:** Přinášíme vám přehled novinek z oboru za měsíc duben. Trh s nemovitostmi roste...
**Očekávaná klasifikace:** `MOVE` — newsletter (hlavička List-Unsubscribe → filtr bez AI)

---

### T06 — Potvrzení objednávky

**Předmět:** Vaše objednávka #88234 byla odeslána
**Tělo:** Vaše objednávka č. 88234 byla předána přepravci GLS. Sledovací číslo: CZ9934821100.
**Očekávaná klasifikace:** `MOVE` — systémová notifikace

---

## KEEP — Osobní B2B nabídky

### T07 — IT poptávka

**Předmět:** Poptávka: IT služby pro naši firmu
**Tělo:** Jmenuji se Petra Horáčková, jednatelka BuildTech s.r.o. Hledáme dodavatele IT služeb — správu serverů a helpdesk pro 15 zaměstnanců. Mohli bychom si domluvit call příští týden?
**Očekávaná klasifikace:** `KEEP` — osobní B2B poptávka

---

### T08 — Účetní spolupráce

**Předmět:** Nabídka spolupráce — účetní služby pro vaši firmu
**Tělo:** Jsem Martin Novák, certifikovaný účetní s 15 lety praxe. Hledám nové klienty pro dlouhodobou spolupráci. Nabízím vedení účetnictví za pevnou měsíční cenu. Mohli bychom se pobavit o podmínkách?
**Očekávaná klasifikace:** `KEEP` — osobní nabídka spolupráce

---

### T09 — Zájem o schůzku

**Předmět:** Zájem o vaše služby — rádi bychom se sešli
**Tělo:** Narážím na vás přes doporučení od Tomáše Beneše. Naše firma hledá partnera pro vývoj interního CRM systému. Máme rozpočet a jasnou specifikaci. Jste k dispozici na krátkou schůzku?
**Očekávaná klasifikace:** `KEEP` — osobní poptávka s doporučením

---

### T10 — Nabídka nábytku (hraniční)

**Předmět:** Dodávka kancelářského nábytku — cenová nabídka
**Tělo:** Na základě vašeho inzerátu vám zasílám cenovou nabídku na dodávku kancelářského nábytku. Nabízíme ergonomické židle a stoly s montáží a zárukou 5 let. Rádi vám připravíme nabídku na míru.
**Očekávaná klasifikace:** `KEEP` — adresovaná nabídka (hraniční případ)

---

## Výsledky testů

| Test | Klasifikace správná? | Akce provedena? | Poznámka |
| ---- | -------------------- | --------------- | -------- |
| T01  |                      |                 |          |
| T02  |                      |                 |          |
| T03  |                      |                 |          |
| T04  |                      |                 |          |
| T05  |                      |                 |          |
| T06  |                      |                 |          |
| T07  |                      |                 |          |
| T08  |                      |                 |          |
| T09  |                      |                 |          |
| T10  |                      |                 |          |
