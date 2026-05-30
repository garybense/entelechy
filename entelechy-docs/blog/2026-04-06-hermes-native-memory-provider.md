---
title: "Entelechy Is Now a Native Memory Provider in Hermes Agent"
authors: [benfrank241]
date: 2026-04-06
tags: [hermes, memory, entelechy, integration]
description: "Hermes Agent now supports pluggable memory providers. Here's why Entelechy is the backend to use, and how to set it up in two minutes."
image: /img/blog/hermes-native-memory-provider.png
hide_table_of_contents: true
---

![Entelechy is now a native memory provider in Hermes Agent](/img/blog/hermes-native-memory-provider.png)

Hermes Agent now ships with a pluggable memory provider system. Entelechy is one of the supported backends, and it's the one that leads on [the benchmark that actually tests memory at scale](/blog/2026/04/02/beam-sota).

<!-- truncate -->

---

## How It Works

Entelechy integrates at two points in the Hermes lifecycle:

**Before each turn**, Entelechy queues an async prefetch. Relevant memories from your past sessions are retrieved and injected into the system prompt before the LLM sees your message. The model has context from previous conversations without you repeating yourself.

**After each response**, your conversation is retained asynchronously. Entelechy extracts facts, entities, and relationships in the background. What you say in this turn becomes searchable starting the next call.

This is intentional: the prefetch pattern means **memories from the current turn won't appear until the next one**. It keeps every call fast.

---

## Why Entelechy on Hermes

Hermes ships with a built-in memory tool that saves notes to local markdown files. It works, but it captures what the model explicitly decides to write down, not what it implicitly learns from your conversations. Context doesn't accumulate automatically. If you ask Hermes to help you plan a sprint on Monday and then open a new session on Friday, it doesn't remember the project, the team, or the deadline unless you re-establish that context yourself.

Entelechy solves this with persistent memory across conversations. You mention a product launch deadline once. A week later, in a new session on a different topic, Hermes already knows it. You didn't repeat yourself. You didn't paste in context. It was recalled automatically.

Of all the supported memory providers, Entelechy is the only one with published results on [BEAM](/blog/2026/04/02/beam-sota), the benchmark that tests memory at 10 million tokens, where context stuffing is physically impossible. Entelechy scores 64.1% at that tier. The next-best published result is 40.6%.

---

## Setting It Up

Setup is a single wizard command:

```bash
hermes memory setup    # select "entelechy"
```

Then confirm memory is active:

```bash
hermes memory status
```

Config lives at `$HERMES_HOME/entelechy/config.json`:

| Key | Default | Description |
|-----|---------|-------------|
| `mode` | `cloud` | `cloud` or `local` |
| `bank_id` | `hermes` | Memory bank identifier |
| `budget` | `mid` | Recall thoroughness: `low` / `mid` / `high` |
| `memory_mode` | `hybrid` | `hybrid`, `context`, or `tools` — see below |
| `prefetch_method` | `recall` | `recall` (fast) or `reflect` (LLM-synthesized) |

---

## Memory Modes

Auto-recall is the core behavior: before every turn, Entelechy automatically fetches relevant memories from your history and injects them into the system prompt. Hermes has the context it needs without the model calling any tool and without you repeating yourself. It happens transparently on every call.

The `memory_mode` setting controls whether auto-recall is active and whether explicit tools are also exposed:

| Mode | Behavior |
|------|----------|
| `hybrid` (default) | Memories auto-injected before every turn, plus `entelechy_recall`, `entelechy_retain`, and `entelechy_reflect` tools exposed to the model |
| `context` | Auto-recall only — memories injected automatically, no tools visible to the model |
| `tools` | Explicit tools only — model must call `entelechy_recall` to retrieve memories; nothing is injected automatically |

`prefetch_method` controls how memories are retrieved during auto-recall:
- **`recall`** (default): semantic search, keyword matching, entity graph traversal, and reranking. Fast.
- **`reflect`**: LLM synthesizes a coherent summary across all relevant memories. Slower, but more useful for complex context.

---

## Migrating from the Old Plugin

If you previously installed `entelechy-hermes` as a pip plugin (the approach from our [earlier guide](/blog/2026/03/17/hermes-agent-memory)), uninstall it first:

```bash
uv pip uninstall entelechy-hermes --python $HOME/.hermes/hermes-agent/venv/bin/python
```

Then run the setup wizard to configure the native provider:

```bash
hermes memory setup
```

The native provider replaces everything the plugin did, with better lifecycle management and the full `memory_mode` and `prefetch_method` controls.

---

## Local or Cloud

In local mode, Entelechy runs an embedded server with built-in PostgreSQL. The daemon starts automatically in the background on first use; no manual setup required. You need an LLM API key for memory extraction:

```json
{
  "mode": "local",
  "llm_provider": "groq",
  "llm_api_key": "your-groq-key"
}
```

The daemon starts when Hermes displays "starting agent" on your first message — not at launch. On a fresh system this can take over a minute while the embedded PostgreSQL server initializes. Subsequent startups are fast. Startup logs land at `~/.hermes/logs/entelechy-embed.log` if you need to debug.

For persistent memory across machines or shared across multiple Hermes instances, use cloud mode instead. Both modes use the same API. Switching is a one-line config change, not a migration.

---

## Get Started

- **Hermes integration docs**: [/sdks/integrations/hermes](/sdks/integrations/hermes)
- **BEAM benchmark results**: [Entelechy Is #1 on BEAM](/blog/2026/04/02/beam-sota)
- **Quick start**: [/developer/api/quickstart](/developer/api/quickstart)
- **GitHub**: [github.com/garybense/entelechy](https://github.com/garybense/entelechy)
- **Cloud**: [ui.mindmods.org/signup](https://ui.mindmods.org/signup)
