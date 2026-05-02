#!/bin/bash
set -e

# Regenerate entelechy-docs/static/bank-template-schema.json from the
# BankTemplateManifest Pydantic model. This file is the source of truth
# for Ajv validation in entelechy-docs/scripts/check-templates.mjs and
# is served verbatim at /bank-template-schema.json on the docs site.

cd "$(dirname "$0")/.."

echo "Generating bank template JSON Schema..."
cd entelechy-dev
uv run generate-bank-template-schema

echo ""
echo "Bank template schema generated successfully!"
