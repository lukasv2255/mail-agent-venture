#!/bin/bash
# PostToolUse hook: kontrola Python syntaxe po každém editu .py souboru
# Výstup chyby jde do Clauda jako feedback — opraví to sám

PAYLOAD=$(cat)
FILE=$(echo "$PAYLOAD" | jq -r '.tool_input.file_path // empty')

# Přeskoč pokud nejde o .py soubor nebo soubor neexistuje
[[ "$FILE" != *.py ]] && exit 0
[[ ! -f "$FILE" ]] && exit 0

python3 -m py_compile "$FILE" 2>&1
if [ $? -ne 0 ]; then
  echo "SYNTAX ERROR v $FILE — oprav před pokračováním." >&2
  exit 1
fi

exit 0
