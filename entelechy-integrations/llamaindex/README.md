# entelechy-llamaindex

LlamaIndex integration for [Entelechy](https://github.com/vectorize-io/entelechy) — persistent long-term memory for AI agents.

Provides two complementary patterns:

- **Tools** (`EntelechyToolSpec`) — Agent-driven memory via LlamaIndex's `BaseToolSpec`. The agent decides when to retain/recall/reflect.
- **Memory** (`EntelechyMemory`) — Automatic memory via LlamaIndex's `BaseMemory` interface. Messages are stored on every turn and recalled as context.

## Installation

```bash
pip install entelechy-llamaindex
```

## Quick Start: Agent Tools

```python
import asyncio
from entelechy_client import Entelechy
from entelechy_llamaindex import EntelechyToolSpec
from llama_index.llms.openai import OpenAI
from llama_index.core.agent import ReActAgent

async def main():
    client = Entelechy(base_url="http://localhost:8888")

    spec = EntelechyToolSpec(
        client=client,
        bank_id="user-123",
        mission="Track user preferences",
    )
    tools = spec.to_tool_list()

    agent = ReActAgent(tools=tools, llm=OpenAI(model="gpt-4o"))
    response = await agent.run("Remember that I prefer dark mode")
    print(response)

asyncio.run(main())
```

## Quick Start: Automatic Memory

```python
from entelechy_client import Entelechy
from entelechy_llamaindex import EntelechyMemory

client = Entelechy(base_url="http://localhost:8888")
memory = EntelechyMemory.from_client(
    client=client,
    bank_id="user-123",
    mission="Track user preferences",
)

agent = ReActAgent(tools=tools, llm=llm, memory=memory)
```

## Configuration

```python
from entelechy_llamaindex import configure

configure(
    entelechy_api_url="http://localhost:8888",
    api_key="your-api-key",
    budget="mid",
    tags=["source:llamaindex"],
    context="my-app",
    mission="Track user preferences",
)
```

## Requirements

- Python 3.10+
- `llama-index-core >= 0.11.0`
- `entelechy-client >= 0.4.0`

## Documentation

- [Integration docs](https://docs.entelechy.vectorize.io/docs/sdks/integrations/llamaindex)
- [Entelechy API docs](https://docs.entelechy.vectorize.io)
