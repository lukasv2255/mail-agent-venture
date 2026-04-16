---
name: security-review
description: Komplexní bezpečnostní audit kódu. Použij při review PR, před deploymenty, nebo když uživatel zmíní bezpečnost, zranitelnosti, nebo audit.
allowed-tools: Read, Grep, Glob
---

# Security Review

Proveď komplexní bezpečnostní analýzu kódu:

## 1. SQL Injection & Query Safety
- Hledej přímé vkládání proměnných do SQL stringů
- Zkontroluj použití ORM a parametrizovaných dotazů

## 2. XSS rizika
- `dangerouslySetInnerHTML` bez sanitizace
- Nekontrolovaný uživatelský vstup v DOM

## 3. Autentizace & Autorizace
- Chybějící auth check před DB operacemi
- Chybějící ownership validace u resources

## 4. Citlivá data
- Logy obsahující hesla, tokeny, PII
- Secrety v kódu nebo env proměnných

## 5. Konfigurace
- Debug mode v produkci
- CORS nastavení
- HTTP headers (CSP, HSTS, X-Frame-Options)

## Výstup

Pro každý nález uveď:
- **Závažnost:** Kritická / Vysoká / Střední / Nízká
- **Soubor a řádek**
- **Popis problému**
- **Konkrétní fix**
