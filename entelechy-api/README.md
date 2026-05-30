# Entelechy API

**Memory System for AI Agents** — Temporal + Semantic + Entity Memory Architecture using PostgreSQL with pgvector.

Entelechy gives AI agents persistent memory that works like human memory: it stores facts, tracks entities and relationships, handles temporal reasoning ("what happened last spring?"), and forms opinions based on configurable disposition traits.

## Installation

```bash
pip install entelechy-api
```

## Quick Start

### Run the Server

```bash
# Set your LLM provider
export ENTELECHY_API_LLM_PROVIDER=openai
export ENTELECHY_API_LLM_API_KEY=sk-xxxxxxxxxxxx

# Start the server (uses embedded PostgreSQL by default)
entelechy-api
```

The server starts at http://localhost:8888 with:
- REST API for memory operations
- MCP server at `/mcp` for tool-use integration

### Use the Python API

```python
from entelechy_api import MemoryEngine

# Create and initialize the memory engine
memory = MemoryEngine()
await memory.initialize()

# Create a memory bank for your agent
bank = await memory.create_memory_bank(
    name="my-assistant",
    background="A helpful coding assistant"
)

# Store a memory
await memory.retain(
    memory_bank_id=bank.id,
    content="The user prefers Python for data science projects"
)

# Recall memories
results = await memory.recall(
    memory_bank_id=bank.id,
    query="What programming language does the user prefer?"
)

# Reflect with reasoning
response = await memory.reflect(
    memory_bank_id=bank.id,
    query="Should I recommend Python or R for this ML project?"
)
```

## CLI Options

```bash
entelechy-api --help

# Common options
entelechy-api --port 9000          # Custom port (default: 8888)
entelechy-api --host 127.0.0.1     # Bind to localhost only
entelechy-api --workers 4          # Multiple worker processes
entelechy-api --log-level debug    # Verbose logging
```

## Configuration

Configure via environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `ENTELECHY_API_DATABASE_URL` | PostgreSQL connection string | `pg0` (embedded) |
| `ENTELECHY_API_LLM_PROVIDER` | `openai`, `anthropic`, `gemini`, `groq`, `ollama`, `lmstudio` | `openai` |
| `ENTELECHY_API_LLM_API_KEY` | API key for LLM provider | - |
| `ENTELECHY_API_LLM_MODEL` | Model name | `gpt-4o-mini` |
| `ENTELECHY_API_HOST` | Server bind address | `0.0.0.0` |
| `ENTELECHY_API_PORT` | Server port | `8888` |

### Example with External PostgreSQL

```bash
export ENTELECHY_API_DATABASE_URL=postgresql://user:pass@localhost:5432/entelechy
export ENTELECHY_API_LLM_PROVIDER=groq
export ENTELECHY_API_LLM_API_KEY=gsk_xxxxxxxxxxxx

entelechy-api
```

## Docker

```bash
docker run --rm -it -p 8888:8888 \
  -e ENTELECHY_API_LLM_API_KEY=$OPENAI_API_KEY \
  -v $HOME/.entelechy-docker:/home/entelechy/.pg0 \
  ghcr.io/garybense/entelechy:latest
```

## MCP Server

For local MCP integration without running the full API server:

```bash
entelechy-local-mcp
```

This runs a stdio-based MCP server that can be used directly with MCP-compatible clients.

## Key Features

- **Multi-Strategy Retrieval (TEMPR)** — Semantic, keyword, graph, and temporal search combined with RRF fusion
- **Entity Graph** — Automatic entity extraction and relationship tracking
- **Temporal Reasoning** — Native support for time-based queries
- **Disposition Traits** — Configurable skepticism, literalism, and empathy influence opinion formation
- **Three Memory Types** — World facts, bank actions, and formed opinions with confidence scores

## Documentation

Full documentation: [https://mindmods.org](https://mindmods.org)

- [Installation Guide](https://mindmods.org/developer/installation)
- [Configuration Reference](https://mindmods.org/developer/configuration)
- [API Reference](https://mindmods.org/api-reference)
- [Python SDK](https://mindmods.org/sdks/python)

## License

Apache 2.0
