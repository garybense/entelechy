---
hide_table_of_contents: true
---

# Strands Integration Changelog

Changelog for [`entelechy-strands`](https://pypi.org/project/entelechy-strands/).

For the source code, see [`entelechy-integrations/strands`](https://github.com/vectorize-io/entelechy/tree/main/entelechy-integrations/strands).

← [Back to main changelog](../index.md)

## [0.1.2](https://github.com/vectorize-io/entelechy/tree/integrations/strands/v0.1.2)

**Improvements**

- Improved Python typing support for the Strands integration by shipping the PEP 561 "py.typed" marker. ([`d054b884`](https://github.com/vectorize-io/entelechy/commit/d054b884))

**Bug Fixes**

- All Strands integration HTTP requests now include a consistent identifying User-Agent for better compatibility and troubleshooting. ([`9372462e`](https://github.com/vectorize-io/entelechy/commit/9372462e))

## [0.1.1](https://github.com/vectorize-io/entelechy/tree/integrations/strands/v0.1.1)

**Features**

- Added Strands Agents SDK integration, enabling Entelechy memory tools to be used with Strands agents. ([`7fe773c0`](https://github.com/vectorize-io/entelechy/commit/7fe773c0))
