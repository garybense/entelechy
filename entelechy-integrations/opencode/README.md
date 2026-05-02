# @vectorize-io/opencode-entelechy

Entelechy memory plugin for [OpenCode](https://opencode.ai) — give your AI coding agent persistent long-term memory across sessions.

## Features

- **Custom tools**: `entelechy_retain`, `entelechy_recall`, `entelechy_reflect` — the agent calls these explicitly
- **Auto-retain**: Captures conversation on `session.idle` and stores to Entelechy
- **Memory injection**: Recalls relevant memories when a new session starts
- **Compaction hook**: Injects memories during context compaction so they survive window trimming

## Quick Start

### 1. Enable the plugin

Add to your `opencode.json` (project) or `~/.config/opencode/opencode.json` (global):

```json
{
  "$schema": "https://opencode.ai/config.json",
  "plugin": ["@vectorize-io/opencode-entelechy"]
}
```

OpenCode auto-installs plugins listed here on startup — no `npm install` required.

### 2. Point to your Entelechy server

```bash
# Self-hosted
export ENTELECHY_API_URL="http://localhost:8888"

# Optional: override the memory bank ID
export ENTELECHY_BANK_ID="my-project"
```

### Using Entelechy Cloud

Get an API key at [ui.entelechy.vectorize.io/connect](https://ui.entelechy.vectorize.io/connect), then either export env vars:

```bash
export ENTELECHY_API_URL="https://api.entelechy.vectorize.io"
export ENTELECHY_API_TOKEN="your-api-key"
```

Or configure inline in `opencode.json`:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "plugin": [
    [
      "@vectorize-io/opencode-entelechy",
      {
        "entelechyApiUrl": "https://api.entelechy.vectorize.io",
        "entelechyApiToken": "your-api-key"
      }
    ]
  ]
}
```

## Configuration

### Plugin Options

Pass options directly in `opencode.json`:

```json
{
  "plugin": [
    [
      "@vectorize-io/opencode-entelechy",
      {
        "entelechyApiUrl": "http://localhost:8888",
        "bankId": "my-project",
        "autoRecall": true,
        "autoRetain": true,
        "recallBudget": "mid"
      }
    ]
  ]
}
```

### Config File

Create `~/.entelechy/opencode.json` for persistent configuration:

```json
{
  "entelechyApiUrl": "http://localhost:8888",
  "entelechyApiToken": "your-api-key",
  "recallBudget": "mid",
  "retainEveryNTurns": 3,
  "debug": false
}
```

### Environment Variables

| Variable                      | Description                         | Default        |
| ----------------------------- | ----------------------------------- | -------------- |
| `ENTELECHY_API_URL`           | Entelechy API base URL              | (required)     |
| `ENTELECHY_API_TOKEN`         | API key for authentication          | (none)         |
| `ENTELECHY_BANK_ID`           | Static memory bank ID               | `opencode`     |
| `ENTELECHY_AGENT_NAME`        | Agent name for dynamic bank IDs     | `opencode`     |
| `ENTELECHY_AUTO_RECALL`       | Auto-recall on session start        | `true`         |
| `ENTELECHY_AUTO_RETAIN`       | Auto-retain on session idle         | `true`         |
| `ENTELECHY_RETAIN_MODE`       | `full-session` or `last-turn`       | `full-session` |
| `ENTELECHY_RECALL_BUDGET`     | Recall budget: `low`, `mid`, `high` | `mid`          |
| `ENTELECHY_RECALL_MAX_TOKENS` | Max tokens for recall results       | `1024`         |
| `ENTELECHY_DYNAMIC_BANK_ID`   | Enable dynamic bank ID derivation   | `false`        |
| `ENTELECHY_BANK_MISSION`      | Bank mission/context                | (none)         |
| `ENTELECHY_DEBUG`             | Enable debug logging                | `false`        |

### Configuration Priority

Settings are loaded in this order (later wins):

1. Built-in defaults
2. `~/.entelechy/opencode.json`
3. Plugin options from `opencode.json`
4. Environment variables

## Tools

### `entelechy_retain`

Store information in long-term memory. The agent uses this to save important facts, user preferences, project context, and decisions.

### `entelechy_recall`

Search long-term memory. The agent uses this proactively before answering questions where prior context would help.

### `entelechy_reflect`

Generate a synthesized answer from long-term memory. Unlike recall (raw memories), reflect produces a coherent summary.

## Dynamic Bank IDs

For multi-project setups, enable dynamic bank ID derivation:

```bash
export ENTELECHY_DYNAMIC_BANK_ID=true
```

The bank ID is composed from granularity fields (default: `agent::project`). Supported fields: `agent`, `project`, `channel`, `user`.

**Note:** The bank ID is derived once when the plugin loads, from environment variables set before OpenCode starts. These dimensions are process-scoped — they don't change per session within a running OpenCode process. For per-user isolation, set the env vars before launching each user's OpenCode instance:

```bash
export ENTELECHY_CHANNEL_ID="slack-general"
export ENTELECHY_USER_ID="user123"
```

## Development

```bash
npm install
npm test        # Run tests
npm run build   # Build to dist/
```

## License

MIT
