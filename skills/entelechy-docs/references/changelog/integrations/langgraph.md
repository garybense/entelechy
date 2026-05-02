---
hide_table_of_contents: true
---

import PageHero from '@site/src/components/PageHero';

<PageHero title="LangGraph Changelog" subtitle="entelechy-langgraph — LangGraph and LangChain memory integration." />

← LangGraph integration

## [0.1.2](https://github.com/vectorize-io/entelechy/tree/integrations/langgraph/v0.1.2)

**Improvements**

- Improved Python typing support for the Entelechy LangGraph integration (added PEP 561 py.typed marker) so type checkers work correctly. ([`d054b884`](https://github.com/vectorize-io/entelechy/commit/d054b884))
- Updated dependencies to address critical/high security vulnerabilities in the Entelechy LangGraph integration. ([`ee4510a7`](https://github.com/vectorize-io/entelechy/commit/ee4510a7))

**Bug Fixes**

- All HTTP requests from the Entelechy LangGraph integration now include a consistent identifying User-Agent header. ([`9372462e`](https://github.com/vectorize-io/entelechy/commit/9372462e))

## [0.1.1](https://github.com/vectorize-io/entelechy/tree/integrations/langgraph/v0.1.1)

**Features**

- Added LangGraph integration for Entelechy. ([`b4320254`](https://github.com/vectorize-io/entelechy/commit/b4320254))
