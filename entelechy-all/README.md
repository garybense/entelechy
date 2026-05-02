# entelechy-all

All-in-one package for Entelechy - Agent Memory That Works Like Human Memory

## Quick Start

```python
from entelechy import start_server, EntelechyClient

# Start server with embedded PostgreSQL
server = start_server(
    llm_provider="groq",
    llm_api_key="your-api-key",
    llm_model="openai/gpt-oss-120b"
)

# Create client
client = EntelechyClient(base_url=server.url)

# Store memories
client.put(agent_id="assistant", content="User prefers Python for data analysis")

# Search memories
results = client.search(agent_id="assistant", query="programming preferences")

# Generate contextual response
response = client.think(agent_id="assistant", query="What languages should I recommend?")

# Stop server when done
server.stop()
```

## Using Context Manager

```python
from entelechy import EntelechyServer, EntelechyClient

with EntelechyServer(llm_provider="groq", llm_api_key="...") as server:
    client = EntelechyClient(base_url=server.url)
    # ... use client ...
# Server automatically stops
```

## Installation

```bash
pip install entelechy-all
```
