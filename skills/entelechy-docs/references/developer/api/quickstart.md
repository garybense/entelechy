
# Quick Start

Get up and running with Entelechy in 60 seconds.

{/* Import raw source files */}

## Clients

<ClientsGrid />

## Start the API Server

### pip (API only)

```bash
pip install entelechy-api
export OPENAI_API_KEY=sk-xxx
export ENTELECHY_API_LLM_API_KEY=$OPENAI_API_KEY

entelechy-api
```

API available at [http://localhost:8888](http://localhost:8888/docs)

### Docker (Full Experience)

```bash

export OPENAI_API_KEY=sk-xxx

docker run --rm -it --pull always -p 8888:8888 -p 9999:9999 \
  -e ENTELECHY_API_LLM_API_KEY=$OPENAI_API_KEY \
  -v $HOME/.entelechy-docker:/home/entelechy/.pg0 \
  ghcr.io/garybense/entelechy:latest
```

- **API**: http://localhost:8888
- **Control Plane** (Web UI): http://localhost:9999

> **💡 LLM Provider**
> 
Entelechy requires an LLM with structured output support. Recommended: **Groq** with `gpt-oss-20b` for fast, cost-effective inference.
See [LLM Providers](../models.md#llm) for more details.
---

## Use the Client

### Python

```bash
pip install entelechy-client
```

```python
from entelechy_client import Entelechy

client = Entelechy(base_url="http://localhost:8888")

# Retain: Store information
client.retain(bank_id="my-bank", content="Alice works at Google as a software engineer")

# Recall: Search memories
client.recall(bank_id="my-bank", query="What does Alice do?")

# Reflect: Generate disposition-aware response
client.reflect(bank_id="my-bank", query="Tell me about Alice")
```

### Node.js

```bash
npm install @garybense/entelechy-client
```

```javascript
import { EntelechyClient } from '@garybense/entelechy-client';

const client = new EntelechyClient({ baseUrl: 'http://localhost:8888' });

// Retain: Store information
await client.retain('my-bank', 'Alice works at Google as a software engineer');

// Recall: Search memories
await client.recall('my-bank', 'What does Alice do?');

// Reflect: Generate response
await client.reflect('my-bank', 'Tell me about Alice');
```

### CLI

```bash
curl -fsSL https://mindmods.org/get-cli | bash
```

```bash
# Retain: Store information
entelechy memory retain my-bank "Alice works at Google as a software engineer"

# Recall: Search memories
entelechy memory recall my-bank "What does Alice do?"

# Reflect: Generate response
entelechy memory reflect my-bank "Tell me about Alice"
```

### Go

```bash
go get github.com/garybense/entelechy/entelechy-clients/go
```

```go
# Section 'quickstart-full' not found in api/quickstart.go
```

---

## What's Happening

| Operation | What it does |
|-----------|--------------|
| **Retain** | Content is processed, facts are extracted, entities are identified and linked in a knowledge graph |
| **Recall** | Four search strategies (semantic, keyword, graph, temporal) run in parallel to find relevant memories |
| **Reflect** | Retrieved memories are used to generate a disposition-aware response |

---

## Integrations

Browse all supported integrations in the Integrations Hub.

## Next Steps

- [**Retain**](./retain) — Advanced options for storing memories
- [**Recall**](./recall) — Search and retrieval strategies
- [**Reflect**](./reflect) — Disposition-aware reasoning
- [**Memory Banks**](./memory-banks) — Configure disposition and mission
- [**Server Deployment**](../installation.md) — Docker Compose, Helm, and production setup
