---
paths:
  - "src/auth/**"
  - "src/api/**"
  - "app/api/**"
  - "src/lib/db/**"
---

# Bezpečnostní pravidla

## Absolutní zákazy

- Nikdy necommituj `.env` soubory
- Nikdy neloguj hesla, tokeny, nebo PII data
- Nikdy nepoužívej `eval()` nebo `new Function()`
- Nikdy nevkládej uživatelský vstup přímo do SQL (použij parametrizované dotazy)

## Auth a sessions

- Kontroluj autentizaci PŘED každou DB operací
- Kontroluj autorizaci (ownership) na každém resource endpointu
- Session tokeny: httpOnly cookies, secure flag v produkci

## Citlivé oblasti (nebezpečné zóny)

`src/auth/` — autentizace a autorizace, dvojitě kontroluj každou změnu
`src/lib/db/` — databázové dotazy, SQL injection riziko
`app/api/` — API endpointy, vždy validuj vstup

## OWASP Top 10 — co kontrolovat

1. SQL Injection → parametrizované dotazy
2. XSS → escapuj output, nepoužívej `dangerouslySetInnerHTML`
3. Broken Auth → kontroluj token platnost a scope
4. Sensitive Data → nešifrovaná data v DB nebo logu
5. Security Misconfiguration → debug mode v produkci
