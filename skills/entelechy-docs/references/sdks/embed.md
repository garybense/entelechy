---
sidebar_position: 5
---

# Daemon CLI (entelechy-embed)

Zero-configuration local memory system with automatic daemon management. Perfect for development, prototyping, and single-user applications.

## Overview

`entelechy-embed` is a zero-configuration SDK that wraps the Entelechy API and PostgreSQL database into a single auto-managed local daemon. It's designed for development, prototyping, and single-user applications where you want memory capabilities without infrastructure overhead.

**How it works:**

1. **First command triggers startup**: When you run any `entelechy-embed` command, it checks if a local daemon is running
2. **Auto-daemon management**: If no daemon exists, it automatically spawns `entelechy-api --daemon` in the background
3. **Embedded database**: The daemon uses `pg0` (embedded PostgreSQL) — no separate database installation required
4. **Command forwarding**: Your command is forwarded to the local daemon via HTTP (localhost:8888)
5. **Auto-shutdown**: After 5 minutes of inactivity (configurable), the daemon gracefully shuts down to free resources

**Key features:**

- **Zero setup** — One `configure` command and you're ready
- **Automatic lifecycle** — Daemon starts on-demand, stops when idle
- **Isolated storage** — Each bank gets its own embedded PostgreSQL database
- **Local-only** — Binds to `127.0.0.1:8888`, not accessible from network
- **Production-grade engine** — Uses the same memory engine as the full API service

Think of it as SQLite for long-term memory — all the power of Entelechy without managing servers.

## Installation

Install via `uvx` (recommended - always latest version):

```bash
# Run directly without installation
uvx entelechy-embed@latest configure

# Or use pipx for persistent installation
pipx install entelechy-embed
```

## Quick Start

### 1. Configure

```bash
# Interactive configuration
entelechy-embed configure

# Or non-interactive via environment variables
export ENTELECHY_EMBED_LLM_PROVIDER=openai
export ENTELECHY_EMBED_LLM_API_KEY=sk-xxxxxxxxxxxx
export ENTELECHY_EMBED_LLM_MODEL=gpt-4o-mini
entelechy-embed configure
```

Configuration is saved to `~/.entelechy/embed`:

```bash
ENTELECHY_EMBED_LLM_PROVIDER=openai
ENTELECHY_EMBED_LLM_MODEL=gpt-4o-mini
ENTELECHY_EMBED_BANK_ID=default
ENTELECHY_EMBED_LLM_API_KEY=sk-xxxxxxxxxxxx

# Daemon settings (macOS: force CPU to avoid MPS/XPC issues)
ENTELECHY_API_EMBEDDINGS_LOCAL_FORCE_CPU=1
ENTELECHY_API_RERANKER_LOCAL_FORCE_CPU=1
```

### 2. Use Memory Operations

```bash
# Store a memory
entelechy-embed memory retain default "User prefers dark mode"

# Query memories
entelechy-embed memory recall default "user preferences"

# Reasoning with memory
entelechy-embed memory reflect default "What color scheme should I use?"
```

The daemon starts automatically on first use!

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ENTELECHY_EMBED_LLM_API_KEY` | **Required**. API key for LLM provider | - |
| `ENTELECHY_EMBED_LLM_PROVIDER` | LLM provider: `openai`, `anthropic`, `gemini`, `groq`, `minimax`, `ollama` | `openai` |
| `ENTELECHY_EMBED_LLM_MODEL` | Model name | `gpt-4o-mini` |
| `ENTELECHY_EMBED_BANK_ID` | Default memory bank ID | `default` |
| `ENTELECHY_EMBED_DAEMON_IDLE_TIMEOUT` | Seconds before daemon auto-exits when idle (0 = never) | `0` |

**Provider Examples:**

```bash
# OpenAI
export ENTELECHY_EMBED_LLM_PROVIDER=openai
export ENTELECHY_EMBED_LLM_API_KEY=sk-xxxxxxxxxxxx
export ENTELECHY_EMBED_LLM_MODEL=gpt-4o

# Groq (fast inference)
export ENTELECHY_EMBED_LLM_PROVIDER=groq
export ENTELECHY_EMBED_LLM_API_KEY=gsk_xxxxxxxxxxxx
export ENTELECHY_EMBED_LLM_MODEL=llama-3.3-70b-versatile

# Anthropic
export ENTELECHY_EMBED_LLM_PROVIDER=anthropic
export ENTELECHY_EMBED_LLM_API_KEY=sk-ant-xxxxxxxxxxxx
export ENTELECHY_EMBED_LLM_MODEL=claude-sonnet-4-20250514
```

## Daemon Management

### Idle Timeout

Customize how long the daemon stays alive when idle:

```bash
# Never timeout (daemon runs until manually stopped)
export ENTELECHY_EMBED_DAEMON_IDLE_TIMEOUT=0

# Shorter timeout: 1 minute
export ENTELECHY_EMBED_DAEMON_IDLE_TIMEOUT=60

# Longer timeout: 30 minutes
export ENTELECHY_EMBED_DAEMON_IDLE_TIMEOUT=1800
```

### Daemon Commands

```bash
# Check daemon status
entelechy-embed daemon status

# View daemon logs in real-time
entelechy-embed daemon logs -f

# Stop daemon manually
entelechy-embed daemon stop
```

## Commands

All memory operations follow the same interface as the CLI:

### Retain (Store Memory)

```bash
entelechy-embed memory retain <bank_id> "content"

# With context
entelechy-embed memory retain <bank_id> "content" --context "source information"

# Background processing
entelechy-embed memory retain <bank_id> "content" --async
```

### Recall (Search)

```bash
entelechy-embed memory recall <bank_id> "query"

# With budget control
entelechy-embed memory recall <bank_id> "query" --budget high

# Show trace
entelechy-embed memory recall <bank_id> "query" --trace
```

### Reflect (Generate Response)

```bash
entelechy-embed memory reflect <bank_id> "prompt"

# With additional context
entelechy-embed memory reflect <bank_id> "prompt" --context "additional info"
```

### Bank Management

```bash
# List all banks
entelechy-embed bank list

# View bank stats
entelechy-embed bank stats <bank_id>

# Set bank name
entelechy-embed bank name <bank_id> "My Assistant"

# Set bank mission
entelechy-embed bank mission <bank_id> "I am a helpful AI assistant"
```

## Troubleshooting

### Daemon Won't Start

Check the daemon logs:

```bash
entelechy-embed daemon logs
# Or watch in real-time
entelechy-embed daemon logs -f
```

Common issues:
- **Missing API key**: Set `ENTELECHY_EMBED_LLM_API_KEY`
- **Port conflict**: Another service using port 8888
- **Permissions**: Check `~/.entelechy/` directory permissions

### Daemon Exits Immediately

Check if you have the idle timeout set too low:

```bash
# Disable idle timeout for debugging
export ENTELECHY_EMBED_DAEMON_IDLE_TIMEOUT=0
entelechy-embed daemon status
```

### Reset Configuration

```bash
# Remove config file and reconfigure
rm ~/.entelechy/embed
entelechy-embed configure
```

## When to Use

**Perfect for:**
- Development and prototyping
- Single-user applications
- Local-first tools
- Quick experiments with Entelechy

**Not suitable for:**
- Production multi-user deployments
- Network-accessible services
- High-availability requirements
- Multi-tenant applications

For production deployments, use the [API Service](../developer/services.md) with external PostgreSQL instead.
