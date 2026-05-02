#!/bin/bash
# Directives API examples for Entelechy CLI
# Run: bash examples/api/directives.sh

set -e

ENTELECHY_URL="${ENTELECHY_API_URL:-http://localhost:8888}"
BANK_ID="directives-example-bank"

# =============================================================================
# Setup (not shown in docs)
# =============================================================================
entelechy bank create "$BANK_ID" --name "Test Bank"

# =============================================================================
# Doc Examples
# =============================================================================

# [docs:create-directive]
# Create a directive (hard rule for reflect)
entelechy directive create "$BANK_ID" \
  "Formal Language" \
  "Always respond in formal English, avoiding slang and colloquialisms."
# [/docs:create-directive]

# Get the directive ID for subsequent operations
DIRECTIVE_ID=$(entelechy directive list "$BANK_ID" -o json | python3 -c "import sys,json; items=json.load(sys.stdin).get('items',[]); print(items[0]['id'] if items else '')" 2>/dev/null || echo "")

# [docs:list-directives]
# List all directives in a bank
entelechy directive list "$BANK_ID"
# [/docs:list-directives]

if [ -n "$DIRECTIVE_ID" ]; then
  # [docs:update-directive]
  # Update a directive (e.g., disable without deleting)
  entelechy directive update "$BANK_ID" "$DIRECTIVE_ID" --is-active false
  # [/docs:update-directive]

  # [docs:delete-directive]
  # Delete a directive
  entelechy directive delete "$BANK_ID" "$DIRECTIVE_ID" -y
  # [/docs:delete-directive]
fi

# =============================================================================
# Cleanup (not shown in docs)
# =============================================================================
entelechy bank delete "$BANK_ID" -y

echo "directives.sh: All examples passed"
