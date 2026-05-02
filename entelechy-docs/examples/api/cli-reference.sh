#!/bin/bash
# CLI Reference examples for Entelechy
# Tests all documented CLI commands and flags
# Run: bash examples/api/cli-reference.sh

set -e

ENTELECHY_URL="${ENTELECHY_API_URL:-http://localhost:8888}"
BANK_ID="cli-test-bank"
DOC_ID="test-document-001"

# =============================================================================
# Setup
# =============================================================================
entelechy configure --api-url "$ENTELECHY_URL"

# Create test data with a known document ID
entelechy memory retain "$BANK_ID" "Alice works at Google as a software engineer" --doc-id "$DOC_ID"
entelechy memory retain "$BANK_ID" "Bob is a data scientist who collaborates with Alice" --doc-id "$DOC_ID"
entelechy memory retain "$BANK_ID" "Alice and Bob work on machine learning projects"
# Create document for delete test early so it has time to index
entelechy memory retain "$BANK_ID" "Carol is a project manager who coordinates the engineering team" --doc-id "temp-doc-to-delete"

# Wait for memories to be indexed (LLM processing takes time)
sleep 5

# =============================================================================
# Configuration (cli.md - Configuration section)
# =============================================================================

# [docs:cli-configure]
entelechy configure --api-url http://localhost:8888
# [/docs:cli-configure]


# =============================================================================
# Core Memory Commands (cli.md - Core Commands section)
# =============================================================================

# [docs:cli-retain-basic]
entelechy memory retain $BANK_ID "Alice works at Google as a software engineer"
# [/docs:cli-retain-basic]


# [docs:cli-retain-context]
entelechy memory retain $BANK_ID "Bob loves hiking" --context "hobby discussion"
# [/docs:cli-retain-context]


# [docs:cli-retain-async]
entelechy memory retain $BANK_ID "Meeting notes" --async
# [/docs:cli-retain-async]


# [docs:cli-recall-basic]
entelechy memory recall $BANK_ID "What does Alice do?"
# [/docs:cli-recall-basic]


# [docs:cli-recall-options]
entelechy memory recall $BANK_ID "hiking recommendations" \
  --budget high \
  --max-tokens 8192
# [/docs:cli-recall-options]


# [docs:cli-recall-fact-type]
entelechy memory recall $BANK_ID "query" --fact-type world,opinion
# [/docs:cli-recall-fact-type]


# [docs:cli-recall-trace]
entelechy memory recall $BANK_ID "query" --trace
# [/docs:cli-recall-trace]


# [docs:cli-reflect-basic]
entelechy memory reflect $BANK_ID "What do you know about Alice?"
# [/docs:cli-reflect-basic]


# [docs:cli-reflect-context]
entelechy memory reflect $BANK_ID "Should I learn Python?" --context "career advice"
# [/docs:cli-reflect-context]


# [docs:cli-reflect-budget]
entelechy memory reflect $BANK_ID "Summarize my week" --budget high
# [/docs:cli-reflect-budget]


# =============================================================================
# Bank Management (cli.md - Bank Management section)
# =============================================================================

# [docs:cli-bank-list]
entelechy bank list
# [/docs:cli-bank-list]


# [docs:cli-bank-disposition]
entelechy bank disposition $BANK_ID
# [/docs:cli-bank-disposition]


# [docs:cli-bank-stats]
entelechy bank stats $BANK_ID
# [/docs:cli-bank-stats]


# [docs:cli-bank-name]
entelechy bank name $BANK_ID "My Assistant"
# [/docs:cli-bank-name]


# [docs:cli-bank-background]
entelechy bank background $BANK_ID "I am a helpful AI assistant interested in technology"
# [/docs:cli-bank-background]


# [docs:cli-bank-background-no-disposition]
entelechy bank background $BANK_ID "Background text" --no-update-disposition
# [/docs:cli-bank-background-no-disposition]


# =============================================================================
# Document Management (cli.md - Document Management section)
# =============================================================================

# [docs:cli-document-list]
entelechy document list $BANK_ID
# [/docs:cli-document-list]


# [docs:cli-document-get]
entelechy document get $BANK_ID $DOC_ID
# [/docs:cli-document-get]


# [docs:cli-document-delete]
entelechy document delete $BANK_ID temp-doc-to-delete
# [/docs:cli-document-delete]


# =============================================================================
# Entity Management (cli.md - Entity Management section)
# =============================================================================

# [docs:cli-entity-list]
entelechy entity list $BANK_ID
# [/docs:cli-entity-list]


# Get an entity ID from the list output and use it
ENTITY_ID=$(entelechy entity list $BANK_ID -o json 2>/dev/null | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4 || echo "")

if [ -n "$ENTITY_ID" ]; then
    # [docs:cli-entity-get]
    entelechy entity get $BANK_ID $ENTITY_ID
    # [/docs:cli-entity-get]

    # [docs:cli-entity-regenerate]
    entelechy entity regenerate $BANK_ID $ENTITY_ID
    # [/docs:cli-entity-regenerate]
else
    echo "No entities found yet, skipping entity get/regenerate"
fi


# =============================================================================
# Output Formats (cli.md - Output Formats section)
# =============================================================================

# [docs:cli-output-json]
entelechy memory recall $BANK_ID "query" -o json
# [/docs:cli-output-json]


# [docs:cli-output-yaml]
entelechy memory recall $BANK_ID "query" -o yaml
# [/docs:cli-output-yaml]


# =============================================================================
# Global Options (cli.md - Global Options section)
# =============================================================================

# [docs:cli-verbose]
entelechy memory recall $BANK_ID "Alice" -v
# [/docs:cli-verbose]


# [docs:cli-help]
entelechy --help
# [/docs:cli-help]


# [docs:cli-version]
entelechy --version
# [/docs:cli-version]


# =============================================================================
# Cleanup
# =============================================================================
curl -s -X DELETE "${ENTELECHY_URL}/v1/default/banks/${BANK_ID}" > /dev/null

echo "cli-reference.sh: All examples passed"
