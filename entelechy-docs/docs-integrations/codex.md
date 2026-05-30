---
sidebar_position: 6
title: "Codex CLI Persistent Memory with Entelechy | Integration Guide"
description: "Add persistent memory to OpenAI Codex CLI with Entelechy. Three Python hook scripts automatically recall context before each prompt and retain conversations — no workflow changes required."
---

# Codex

[View Changelog →](/changelog/integrations/codex)

Persistent memory for [Codex CLI](https://github.com/openai/codex) using [Entelechy](https://vectorize.io/entelechy). Three Python hook scripts automatically recall relevant context before each prompt and retain conversations after each turn — no changes to your Codex workflow required.

## Quick Start

```bash
curl -fsSL https://mindmods.org/get-codex | bash
```

The installer will guide you through choosing local or cloud mode and configuring your connection. Once installed, start a new Codex session — memory is live.

To uninstall:

```bash
curl -fsSL https://mindmods.org/get-codex | bash -s -- --uninstall
```

## Features

- **Auto-recall** — on every user prompt, queries Entelechy for relevant memories and injects them as `additionalContext` (invisible to the transcript, visible to Codex)
- **Auto-retain** — after each Codex response, stores the conversation transcript to Entelechy for future recall
- **Dynamic bank IDs** — supports per-project memory isolation based on the working directory
- **Session-level upsert** — uses the session ID as the document ID so re-running the same session updates rather than duplicates stored content
- **Zero dependencies** — pure Python stdlib, no pip install required

## Architecture

The plugin uses three Codex hook events:

| Hook | Event | Purpose |
|------|-------|---------|
| `session_start.py` | `SessionStart` | Warm up — verify Entelechy is reachable |
| `recall.py` | `UserPromptSubmit` | **Auto-recall** — query memories, inject as `additionalContext` |
| `retain.py` | `Stop` | **Auto-retain** — extract transcript, POST to Entelechy (async) |

On `UserPromptSubmit`, the hook reads the prompt, queries Entelechy for the most relevant memories, and outputs a `hookSpecificOutput.additionalContext` block. Codex prepends this to the conversation before sending it to the model:

```
<entelechy_memories>
Relevant memories from past conversations...
Current time - 2026-03-27 09:14

- Project uses FastAPI with asyncpg — not SQLAlchemy [world] (2026-03-26)
- Preferred testing framework: pytest with pytest-asyncio [experience] (2026-03-26)
</entelechy_memories>
```

On `Stop`, the hook reads the session transcript, strips previously injected memory tags (to prevent feedback loops), and POSTs the conversation to Entelechy asynchronously.

## Connection Modes

### 1. External API (recommended)

Connect to a running Entelechy server (cloud or self-hosted):

```json
{
  "entelechyApiUrl": "https://api.mindmods.org",
  "entelechyApiToken": "hsk_your_token"
}
```

### 2. Local Daemon

Run `entelechy-embed` locally. The `session_start.py` hook will detect it on `apiPort` (default `9077`). The daemon is not auto-started by the Codex plugin — start it separately:

```bash
uvx entelechy-embed
```

Then leave `entelechyApiUrl` empty in your config and the plugin will connect to `http://localhost:9077`.

## Configuration

Settings are loaded from `~/.entelechy/codex.json`. Every setting can also be overridden via environment variable.

**Loading order** (later entries win):

1. Built-in defaults
2. Plugin `settings.json` (at `~/.entelechy/codex/settings.json`)
3. User config (`~/.entelechy/codex.json`)
4. Environment variables

---

### Connection

| Setting | Env Var | Default | Description |
|---------|---------|---------|-------------|
| `entelechyApiUrl` | `ENTELECHY_API_URL` | `""` | URL of the Entelechy API server. Required. |
| `entelechyApiToken` | `ENTELECHY_API_TOKEN` | `null` | API token for authentication. Required for Entelechy Cloud. |
| `apiPort` | `ENTELECHY_API_PORT` | `9077` | Port for the local `entelechy-embed` daemon. |

---

### Memory Bank

| Setting | Env Var | Default | Description |
|---------|---------|---------|-------------|
| `bankId` | `ENTELECHY_BANK_ID` | `"codex"` | The bank to read from and write to. All sessions share this bank unless `dynamicBankId` is enabled. |
| `bankMission` | `ENTELECHY_BANK_MISSION` | coding assistant prompt | Describes the agent's purpose. Sent when creating or updating the bank. |
| `retainMission` | — | extraction prompt | Instructions for Entelechy's fact extraction — what to extract from coding conversations. |
| `dynamicBankId` | `ENTELECHY_DYNAMIC_BANK_ID` | `false` | When `true`, derives a unique bank ID from `dynamicBankGranularity` fields — useful for per-project isolation. |
| `dynamicBankGranularity` | — | `["agent", "project"]` | Which fields to combine for dynamic bank IDs. `"project"` = working directory, `"agent"` = agent name. |
| `bankIdPrefix` | — | `""` | Prefix prepended to all bank IDs. |
| `agentName` | `ENTELECHY_AGENT_NAME` | `"codex"` | Agent name used in dynamic bank ID derivation. |

---

### Auto-Recall

| Setting | Env Var | Default | Description |
|---------|---------|---------|-------------|
| `autoRecall` | `ENTELECHY_AUTO_RECALL` | `true` | Master switch for auto-recall. |
| `recallBudget` | `ENTELECHY_RECALL_BUDGET` | `"mid"` | Search depth: `"low"` (fast), `"mid"` (balanced), `"high"` (thorough). |
| `recallMaxTokens` | `ENTELECHY_RECALL_MAX_TOKENS` | `1024` | Max tokens in the recalled memory block. |
| `recallTypes` | — | `["world", "experience"]` | Memory types to retrieve. |
| `recallContextTurns` | `ENTELECHY_RECALL_CONTEXT_TURNS` | `1` | Prior turns to include when building the recall query. `1` = latest prompt only. |
| `recallMaxQueryChars` | `ENTELECHY_RECALL_MAX_QUERY_CHARS` | `800` | Max characters in the query sent to Entelechy. |
| `recallRoles` | — | `["user", "assistant"]` | Which roles to include when building a multi-turn query. |
| `recallPromptPreamble` | — | built-in | Text placed above the recalled memories in the injected context block. |

---

### Auto-Retain

| Setting | Env Var | Default | Description |
|---------|---------|---------|-------------|
| `autoRetain` | `ENTELECHY_AUTO_RETAIN` | `true` | Master switch for auto-retain. |
| `retainMode` | `ENTELECHY_RETAIN_MODE` | `"full-session"` | `"full-session"` sends the full transcript per session (upserted by session ID). `"chunked"` sends sliding windows every N turns. |
| `retainEveryNTurns` | — | `10` | Retain fires every N turns. `1` = every turn. Higher values reduce API calls. |
| `retainOverlapTurns` | — | `2` | Extra turns included from the previous chunk (chunked mode only). |
| `retainRoles` | — | `["user", "assistant"]` | Which roles to include in the retained transcript. |
| `retainTags` | — | `["{session_id}"]` | Tags attached to the stored document. `{session_id}` is replaced at runtime. |
| `retainMetadata` | — | `{}` | Arbitrary key-value metadata attached to the stored document. |
| `retainContext` | — | `"codex"` | Label identifying the source integration. Useful when multiple integrations write to the same bank. |

---

### Debug

| Setting | Env Var | Default | Description |
|---------|---------|---------|-------------|
| `debug` | `ENTELECHY_DEBUG` | `false` | Enable verbose logging to stderr. All log lines are prefixed with `[Entelechy]`. |

## Per-Project Memory

To give each project its own isolated memory bank, enable dynamic bank IDs:

```json
{
  "dynamicBankId": true,
  "dynamicBankGranularity": ["agent", "project"]
}
```

With this config, running Codex in `~/projects/api` and `~/projects/frontend` stores and recalls memories separately. Bank IDs are derived from the working directory path.

## Troubleshooting

**Hooks not firing**: Check that `~/.codex/config.toml` contains `codex_hooks = true` under `[features]`. Re-run the installer to fix this automatically.

**No memories recalled**: Recall returns results only after something has been retained. Either complete one Codex session first, or seed your bank manually using the [cookbook example](https://github.com/garybense/entelechy-cookbook/tree/main/applications/codex-memory).

**Memory not being stored**: `retainEveryNTurns` defaults to `10` — retain only fires every 10 turns. While testing, add `"retainEveryNTurns": 1` to `~/.entelechy/codex.json`.

**Debug mode**: Add `"debug": true` to `~/.entelechy/codex.json` to see what Entelechy is doing on each turn:

```
[Entelechy] Recalling from bank 'codex', query length: 42
[Entelechy] Injecting 3 memories
[Entelechy] Retaining to bank 'codex', doc 'sess-abc123', 2 messages, 847 chars
```

**High latency on recall**: Use `"recallBudget": "low"` or reduce `recallMaxTokens` to speed up recall queries.
