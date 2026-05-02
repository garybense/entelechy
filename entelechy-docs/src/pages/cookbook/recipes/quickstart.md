---
sidebar_position: 1
---

# Entelechy Quickstart


:::tip Run this notebook
This recipe is available as an interactive Jupyter notebook.
[**Open in GitHub →**](https://github.com/vectorize-io/entelechy-cookbook/blob/main/notebooks/01-quickstart.ipynb)
:::


This notebook covers the basics of using Entelechy:
- **Retain**: Store information in memory
- **Recall**: Retrieve memories matching a query
- **Reflect**: Generate insights from memories

## Prerequisites

Make sure you have Entelechy running. The easiest way is via Docker:

```bash
export OPENAI_API_KEY=your-key

docker run --rm -it --pull always -p 8888:8888 -p 9999:9999 \
  -e ENTELECHY_API_LLM_API_KEY=$OPENAI_API_KEY \
  -e ENTELECHY_API_LLM_MODEL=o3-mini \
  -v $HOME/.entelechy-docker:/home/entelechy/.pg0 \
  ghcr.io/vectorize-io/entelechy:latest
```

- API: http://localhost:8888
- UI: http://localhost:9999

## Installation

Install the Entelechy Python client:


```python
!pip install entelechy-client nest_asyncio python-dotenv -U
```

## Connect to Entelechy


```python
# Jupyter notebooks already run an asyncio event loop. The entelechy client 
# uses loop.run_until_complete() internally, but Python doesn't allow nested 
# event loops by default. nest_asyncio patches this to allow nesting.
import nest_asyncio
nest_asyncio.apply()

import os
from dotenv import load_dotenv

# Load environment variables from .env file
# Copy .env.example to .env and fill in your values
load_dotenv()

# Configuration (override with env vars if set)
ENTELECHY_API_URL = os.getenv("ENTELECHY_API_URL", "http://localhost:8888")
ENTELECHY_UI_URL = os.getenv("ENTELECHY_UI_URL", "http://localhost:9999")

from entelechy_client import Entelechy

client = Entelechy(base_url=ENTELECHY_API_URL)
```

## Retain: Store Information

The `retain` operation is used to push new memories into Entelechy. It tells Entelechy to _retain_ the information you pass in.

Behind the scenes, the retain operation uses an LLM to extract key facts, temporal data, entities, and relationships.


```python
# Simple retain
client.retain(
    bank_id="my-bank",
    content="Alice works at Google as a software engineer"
)

# View the stored document in the UI:
print(f"View documents: {ENTELECHY_UI_URL}/banks/my-bank?view=documents")
```


```python
# Retain with context and timestamp
client.retain(
    bank_id="my-bank",
    content="Alice got promoted to senior engineer",
    context="career update",
    timestamp="2025-06-15T10:00:00Z"
)
```

## Recall: Retrieve Memories

The `recall` operation retrieves memories matching a query. It performs 4 retrieval strategies in parallel:
- **Semantic**: Vector similarity
- **Keyword**: BM25 exact matching
- **Graph**: Entity/temporal/causal links
- **Temporal**: Time range filtering


```python
# Simple recall
results = client.recall(bank_id="my-bank", query="What does Alice do?")

print("Memories:")
for r in results.results:
    print(f"  - {r.text}")
```


```python
# Temporal recall
results = client.recall(bank_id="my-bank", query="What happened in June?")

print("Memories:")
for r in results.results:
    print(f"  - {r.text}")
```

## Reflect: Generate Insights

The `reflect` operation performs a more thorough analysis of existing memories. This allows the agent to form new connections between memories which are then persisted as opinions and/or observations.

Example use cases:
- An AI Project Manager reflecting on what risks need to be mitigated
- A Sales Agent reflecting on why certain outreach messages have gotten responses
- A Support Agent reflecting on opportunities where customers have unanswered questions


```python
response = client.reflect(bank_id="my-bank", query="What should I know about Alice?")
print(response)
```

## Memory Types

Entelechy organizes memory into four networks to mimic human memory:

- **World**: Facts about the world ("The stove gets hot")
- **Experiences**: Agent's own experiences ("I touched the stove and it really hurt")
- **Opinion**: Beliefs with confidence scores ("I shouldn't touch the stove again" - .99 confidence)
- **Observation**: Complex mental models derived by reflecting on facts and experiences

## Cleanup

Delete the bank created during this notebook:


```python
import requests

response = requests.delete(f"{ENTELECHY_API_URL}/v1/default/banks/my-bank")
print(f"Deleted my-bank: {response.json()}")
```
