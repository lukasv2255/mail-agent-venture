#!/bin/bash
# Stop hook: zajistí, že testy projdou před dokončením
# DŮLEŽITÉ: Kontroluj stop_hook_active aby nedošlo k nekonečné smyčce

PAYLOAD=$(cat)
STOP_HOOK_ACTIVE=$(echo "$PAYLOAD" | jq -r '.stop_hook_active // false')

# Při druhém pokusu nechej Clauda skončit
if [ "$STOP_HOOK_ACTIVE" = "true" ]; then
  exit 0
fi

# Spusť testy (odkomentuj pro aktivaci)
# npm run test 2>&1
# if [ $? -ne 0 ]; then
#   echo "Testy neprošly. Oprav chyby před dokončením." >&2
#   exit 2
# fi

exit 0
