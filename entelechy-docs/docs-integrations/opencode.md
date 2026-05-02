---
sidebar_position: 20
title: "OpenCode Persistent Memory with Entelechy | Integration"
description: "Add long-term memory to OpenCode with Entelechy. Automatically captures conversations and recalls relevant context across coding sessions."
---

# OpenCode

Persistent long-term memory plugin for [OpenCode](https://opencode.ai) using [Entelechy](https://vectorize.io/entelechy). Automatically captures conversations, recalls relevant context on session start, and provides retain/recall/reflect tools the agent can call directly.

## Quick Start

Add to your `opencode.json` (project) or `~/.config/opencode/opencode.json` (global):

```json
{
  "$schema": "https://opencode.ai/config.json",
  "plugin": ["@vectorize-io/opencode-entelechy"]
}
```

OpenCode auto-installs plugins in the `"plugin"` array on startup — no `npm install` required.

Point the plugin at your Entelechy server and start OpenCode:

```bash
export ENTELECHY_API_URL="http://localhost:8888"
opencode
```

### Using Entelechy Cloud

Get an API key at [ui.entelechy.vectorize.io/connect](https://ui.entelechy.vectorize.io/connect):

```bash
export ENTELECHY_API_URL="https://api.entelechy.vectorize.io"
export ENTELECHY_API_TOKEN="your-api-key"
opencode
```

Or configure inline via plugin options in `opencode.json`:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "plugin": [
    ["@vectorize-io/opencode-entelechy", {
      "entelechyApiUrl": "https://api.entelechy.vectorize.io",
      "entelechyApiToken": "your-api-key"
    }]
  ]
}
```

## Features

### Custom Tools

The plugin registers three tools the agent can call explicitly:

| Tool | Description |
|---|---|
| `entelechy_retain` | Store information in long-term memory |
| `entelechy_recall` | Search long-term memory for relevant information |
| `entelechy_reflect` | Generate a synthesized answer from long-term memory |

### Auto-Retain

When the session goes idle (`session.idle` event), the plugin automatically retains the conversation transcript to Entelechy. Configurable via `retainEveryNTurns` to control frequency.

### Session Recall

When a new session starts, the plugin recalls relevant project context and injects it into the system prompt, giving the agent access to memories from prior sessions.

### Compaction Hook

When OpenCode compacts the context window, the plugin:
1. Retains the current conversation before compaction
2. Recalls relevant memories and injects them into the compaction context

This ensures memories survive context window trimming.

## Configuration

### Plugin Options

```json
{
  "plugin": [
    ["@vectorize-io/opencode-entelechy", {
      "entelechyApiUrl": "http://localhost:8888",
      "entelechyApiToken": "your-api-key",
      "bankId": "my-project",
      "autoRecall": true,
      "autoRetain": true,
      "recallBudget": "mid",
      "recallTags": [],
      "recallTagsMatch": "any",
      "retainTags": [],
      "retainEveryNTurns": 3,
      "debug": false
    }]
  ]
}
```

### Config File

Create `~/.entelechy/opencode.json` for persistent configuration that applies across all projects:

```json
{
  "entelechyApiUrl": "http://localhost:8888",
  "entelechyApiToken": "your-api-key",
  "recallBudget": "mid"
}
```

### Environment Variables

| Variable | Description | Default |
|---|---|---|
| `ENTELECHY_API_URL` | Entelechy API base URL | *(required)* |
| `ENTELECHY_API_TOKEN` | API key for authentication | |
| `ENTELECHY_BANK_ID` | Static memory bank ID | `opencode` |
| `ENTELECHY_AGENT_NAME` | Agent name for dynamic bank IDs | `opencode` |
| `ENTELECHY_AUTO_RECALL` | Auto-recall on session start | `true` |
| `ENTELECHY_AUTO_RETAIN` | Auto-retain on session idle | `true` |
| `ENTELECHY_RETAIN_MODE` | `full-session` or `last-turn` | `full-session` |
| `ENTELECHY_RECALL_BUDGET` | Recall budget: `low`, `mid`, `high` | `mid` |
| `ENTELECHY_RECALL_MAX_TOKENS` | Max tokens for recall results | `1024` |
| `ENTELECHY_RECALL_TAGS` | Comma-separated tags to filter recall results | |
| `ENTELECHY_RECALL_TAGS_MATCH` | Tag match mode: `any`, `all`, `any_strict`, `all_strict` | `any` |
| `ENTELECHY_DYNAMIC_BANK_ID` | Enable dynamic bank ID derivation | `false` |
| `ENTELECHY_BANK_MISSION` | Bank mission/context for reflect | |
| `ENTELECHY_DEBUG` | Enable debug logging to stderr | `false` |

Configuration priority (later wins): defaults < `~/.entelechy/opencode.json` < plugin options < env vars.

## Dynamic Bank IDs

For multi-project isolation, enable dynamic bank ID derivation:

```bash
export ENTELECHY_DYNAMIC_BANK_ID=true
```

The bank ID is composed from granularity fields (default: `agent::project`). Supported fields: `agent`, `project`, `channel`, `user`.

For multi-user scenarios (e.g., shared agent serving multiple users):

```bash
export ENTELECHY_CHANNEL_ID="slack-general"
export ENTELECHY_USER_ID="user123"
```

## How It Works

1. **Plugin loads** when OpenCode starts — creates a `EntelechyClient`, derives the bank ID, and registers tools + hooks
2. **Session starts** — `session.created` event triggers, plugin marks session for recall injection
3. **System transform** — on the first LLM call, recalled memories are injected into the system prompt
4. **Agent works** — can call `entelechy_recall` and `entelechy_retain` explicitly during the session
5. **Session idles** — `session.idle` event triggers auto-retain of the conversation
6. **Compaction** — if the context window fills up, memories are preserved through the compaction
