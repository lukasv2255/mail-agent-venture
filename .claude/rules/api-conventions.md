---
paths:
  - "src/api/**"
  - "src/handlers/**"
  - "src/routes/**"
  - "app/api/**"
---

# API Konvence

## Response shape

Vždy používej jednotný formát:

```typescript
// Úspěch
{ data: T, error: null }

// Chyba
{ data: null, error: { code: string, message: string } }
```

Nikdy neposílej různé struktury pro různé endpointy.

## Validace

- Validuj všechny vstupy pomocí `zod` na začátku handleru
- Vrať `400` pro nevalidní vstup, ne `500`
- Nikdy nevěř `req.body` bez validace

## Chybové kódy

- `400` — bad request (validační chyba)
- `401` — unauthorized (není přihlášen)
- `403` — forbidden (nemá oprávnění)
- `404` — not found
- `409` — conflict (duplicita)
- `500` — server error

## Bezpečnost

- Nikdy neexponuj stack traces nebo interní chyby klientovi
- Sanitizuj vstupy před DB dotazy
- Rate limiting na public endpointech
