#!/bin/bash
# PreToolUse hook: blokuje nebezpečné bash příkazy
# Exit code 2 = zablokuj a pošli chybu Claudovi

PAYLOAD=$(cat)
COMMAND=$(echo "$PAYLOAD" | jq -r '.tool_input.command // ""')

# Nebezpečné vzory
DANGEROUS_PATTERNS=(
  "rm -rf /"
  "rm -rf ~"
  "rm -rf \*"
  "git push --force origin main"
  "git push --force origin master"
  "git push -f origin main"
  "DROP TABLE"
  "DROP DATABASE"
  "truncate"
  "format c:"
  ":(){:|:&};:"
)

for pattern in "${DANGEROUS_PATTERNS[@]}"; do
  if echo "$COMMAND" | grep -qi "$pattern"; then
    echo "BLOCKED: Nebezpečný příkaz detekován: '$pattern'" >&2
    exit 2
  fi
done

exit 0
