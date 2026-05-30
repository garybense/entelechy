---
hide_table_of_contents: true
---

# ag2 Integration Changelog

Changelog for [`entelechy-ag2`](https://pypi.org/project/entelechy-ag2/).

For the source code, see [`entelechy-integrations/ag2`](https://github.com/garybense/entelechy/tree/main/entelechy-integrations/ag2).

← [Back to main changelog](../index.md)

## [0.1.2](https://github.com/garybense/entelechy/tree/integrations/ag2/v0.1.2)

**Improvements**

- Improved type-checking support for the AG2 integration by shipping PEP 561 type information. ([`d054b884`](https://github.com/garybense/entelechy/commit/d054b884))

**Bug Fixes**

- All HTTP requests from the AG2 integration now include an identifying User-Agent header for improved compatibility and observability. ([`9372462e`](https://github.com/garybense/entelechy/commit/9372462e))
- Resolved critical and high-severity security vulnerabilities in dependencies. ([`ee4510a7`](https://github.com/garybense/entelechy/commit/ee4510a7))

## [0.1.1](https://github.com/garybense/entelechy/tree/integrations/ag2/v0.1.1)

**Features**

- Added AG2 framework integration for Entelechy. ([`73123870`](https://github.com/garybense/entelechy/commit/73123870))
