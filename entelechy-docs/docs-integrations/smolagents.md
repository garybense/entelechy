---
sidebar_position: 12
title: "SmolAgents Persistent Memory with Entelechy | Integration"
description: "Add long-term memory to HuggingFace SmolAgents with Entelechy retain, recall, and reflect tools — drop-in Tool subclasses your agent can call directly."
---

# SmolAgents

Persistent memory tools for [SmolAgents](https://github.com/huggingface/smolagents) agents via Entelechy. Give your agents long-term memory with retain, recall, and reflect — using SmolAgents' native Tool pattern.

## Features

- **Native Tool Subclasses** - Each tool extends SmolAgents' `Tool` base class
- **Memory Instructions** - Pre-recall memories for injection into agent system prompt
- **Three Memory Tools** - Retain (store), Recall (search), Reflect (synthesize) — include any combination
- **Factory Function** - Create all tools in one call with shared configuration
- **Simple Configuration** - Configure once globally, or pass a client directly

## Installation

```bash
pip install entelechy-smolagents
```

## Quick Start

```python
from smolagents import CodeAgent, HfApiModel
from entelechy_smolagents import create_entelechy_tools

tools = create_entelechy_tools(
    bank_id="user-123",
    entelechy_api_url="http://localhost:8888",
)

agent = CodeAgent(
    tools=tools,
    model=HfApiModel(),
)

agent.run("Remember that I prefer dark mode")
agent.run("What are my preferences?")
```

The agent now has three tools it can call:

- **`entelechy_retain`** — Store information to long-term memory
- **`entelechy_recall`** — Search long-term memory for relevant facts
- **`entelechy_reflect`** — Synthesize a reasoned answer from memories

## With Memory Instructions

Pre-recall relevant memories and inject them into the system prompt:

```python
from entelechy_smolagents import create_entelechy_tools, memory_instructions

tools = create_entelechy_tools(
    bank_id="user-123",
    entelechy_api_url="http://localhost:8888",
)

memories = memory_instructions(
    bank_id="user-123",
    entelechy_api_url="http://localhost:8888",
)

agent = CodeAgent(
    tools=tools,
    model=HfApiModel(),
    system_prompt=f"You are a helpful assistant.\n\n{memories}",
)
```

## Individual Tools

You can also use the tool classes directly:

```python
from entelechy_smolagents import EntelechyRetainTool, EntelechyRecallTool

agent = CodeAgent(
    tools=[
        EntelechyRetainTool(
            bank_id="user-123",
            entelechy_api_url="http://localhost:8888",
        ),
        EntelechyRecallTool(
            bank_id="user-123",
            entelechy_api_url="http://localhost:8888",
        ),
    ],
    model=HfApiModel(),
)
```

## Selecting Tools

Include only the tools you need via the factory:

```python
tools = create_entelechy_tools(
    bank_id="user-123",
    entelechy_api_url="http://localhost:8888",
    enable_retain=True,
    enable_recall=True,
    enable_reflect=False,  # Omit reflect
)
```

## Global Configuration

Instead of passing connection details to every tool, configure once:

```python
from entelechy_smolagents import configure, create_entelechy_tools

configure(
    entelechy_api_url="http://localhost:8888",
    api_key="your-api-key",       # Or set ENTELECHY_API_KEY env var
    budget="mid",                  # Recall budget: low/mid/high
    max_tokens=4096,               # Max tokens for recall results
    tags=["env:prod"],             # Tags for stored memories
    recall_tags=["scope:global"],  # Tags to filter recall
    recall_tags_match="any",       # Tag match mode: any/all/any_strict/all_strict
)

# Now create tools without passing connection details
tools = create_entelechy_tools(bank_id="user-123")
```

## Configuration Reference

### `create_entelechy_tools()`

| Parameter | Default | Description |
|---|---|---|
| `bank_id` | *required* | Entelechy memory bank ID |
| `client` | `None` | Pre-configured Entelechy client |
| `entelechy_api_url` | `None` | API URL (used if no client provided) |
| `api_key` | `None` | API key (used if no client provided) |
| `budget` | `"mid"` | Recall/reflect budget level (low/mid/high) |
| `max_tokens` | `4096` | Maximum tokens for recall results |
| `tags` | `None` | Tags applied when storing memories |
| `recall_tags` | `None` | Tags to filter when searching |
| `recall_tags_match` | `"any"` | Tag matching mode |
| `enable_retain` | `True` | Include the retain (store) tool |
| `enable_recall` | `True` | Include the recall (search) tool |
| `enable_reflect` | `True` | Include the reflect (synthesize) tool |

### `memory_instructions()`

| Parameter | Default | Description |
|---|---|---|
| `bank_id` | *required* | Entelechy memory bank ID |
| `client` | `None` | Pre-configured Entelechy client |
| `entelechy_api_url` | `None` | API URL (used if no client provided) |
| `api_key` | `None` | API key (used if no client provided) |
| `query` | `"relevant context about the user"` | Recall query for memory injection |
| `budget` | `"low"` | Recall budget level |
| `max_results` | `5` | Maximum memories to inject |
| `max_tokens` | `4096` | Maximum tokens for recall results |
| `prefix` | `"Relevant memories:\n"` | Text prepended before memory list |
| `tags` | `None` | Tags to filter recall results |
| `tags_match` | `"any"` | Tag matching mode |

### `configure()`

| Parameter | Default | Description |
|---|---|---|
| `entelechy_api_url` | Production API | Entelechy API URL |
| `api_key` | `ENTELECHY_API_KEY` env | API key for authentication |
| `budget` | `"mid"` | Default recall budget level |
| `max_tokens` | `4096` | Default max tokens for recall |
| `tags` | `None` | Default tags for retain operations |
| `recall_tags` | `None` | Default tags to filter recall |
| `recall_tags_match` | `"any"` | Default tag matching mode |
| `verbose` | `False` | Enable verbose logging |

## Requirements

- Python >= 3.10
- smolagents
- entelechy-client >= 0.4.0
- A running Entelechy API server
