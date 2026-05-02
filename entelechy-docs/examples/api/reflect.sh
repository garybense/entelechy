#!/bin/bash
# Reflect API examples for Entelechy CLI
# Run: bash examples/api/reflect.sh

set -e

ENTELECHY_URL="${ENTELECHY_API_URL:-http://localhost:8888}"

# =============================================================================
# Setup (not shown in docs)
# =============================================================================
entelechy memory retain my-bank "Alice works at Google as a software engineer"
entelechy memory retain my-bank "Alice has been working there for 5 years"

# =============================================================================
# Doc Examples
# =============================================================================

# [docs:reflect-basic]
entelechy memory reflect my-bank "What do you know about Alice?"
# [/docs:reflect-basic]


# [docs:reflect-with-context]
entelechy memory reflect my-bank "Should I learn Python?" --context "career advice"
# [/docs:reflect-with-context]


# [docs:reflect-with-params]
entelechy memory reflect my-bank "Summarize my week" --budget high --max-tokens 8192
# [/docs:reflect-with-params]


# [docs:reflect-disposition]
entelechy bank set-config my-bank \
  --disposition-skepticism 5 \
  --disposition-literalism 4 \
  --disposition-empathy 2
entelechy memory reflect my-bank "Should I invest in crypto?"
# [/docs:reflect-disposition]


# [docs:reflect-sources]
entelechy memory reflect my-bank "Tell me about Alice" --include-facts
# [/docs:reflect-sources]


# [docs:reflect-with-tags]
entelechy memory reflect my-bank "What feedback did the user give?" \
  --tags "user:alice" --tags-match any_strict
# [/docs:reflect-with-tags]


# [docs:reflect-structured-output]
# First, create a JSON schema file schema.json:
cat > schema.json << 'EOF'
{
  "type": "object",
  "properties": {
    "recommendation": {"type": "string"},
    "confidence": {"type": "string", "enum": ["low", "medium", "high"]},
    "key_factors": {"type": "array", "items": {"type": "string"}}
  },
  "required": ["recommendation", "confidence", "key_factors"]
}
EOF

# Then use the --schema flag:
entelechy memory reflect hiring-team \
  "Should we hire Alice for the ML team lead position?" \
  --schema schema.json

# Cleanup the temporary schema file
rm -f schema.json
# [/docs:reflect-structured-output]


# =============================================================================
# Cleanup (not shown in docs)
# =============================================================================
curl -s -X DELETE "${ENTELECHY_URL}/v1/default/banks/my-bank" > /dev/null

echo "reflect.sh: All examples passed"
