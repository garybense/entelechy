# Entelechy for OpenAI Codex CLI

Long-term memory for [OpenAI Codex CLI](https://github.com/openai/codex) — remembers your projects, preferences, and past sessions across every conversation.

## How it works

Three Codex hooks keep memory in sync automatically:

| Hook | Action |
|------|--------|
| `SessionStart` | Warms up the Entelechy server in the background |
| `UserPromptSubmit` | Recalls relevant memories and injects them into context |
| `Stop` | Retains the conversation to long-term memory |

## Requirements

- **OpenAI Codex CLI** v0.116.0 or later (hooks support)
- **Python 3.9+** (for hook scripts)
- **Entelechy**: [Entelechy Cloud](https://mindmods.org) or local `entelechy-embed`

## Installation

```bash
curl -fsSL https://mindmods.org/get-codex | bash
```

The installer:
1. Downloads scripts to `~/.entelechy/codex/scripts/`
2. Writes `~/.codex/hooks.json` with absolute paths to the scripts
3. Adds `codex_hooks = true` to `~/.codex/config.toml`

### Uninstall

```bash
curl -fsSL https://mindmods.org/get-codex | bash -s -- --uninstall
```

## Configuration

The default config is written to `~/.entelechy/codex/settings.json` on first install.

For personal overrides (stable across updates), create `~/.entelechy/codex.json`:

```json
{
  "entelechyApiUrl": "https://api.mindmods.org",
  "entelechyApiToken": "your-api-key",
  "bankId": "my-codex-memory"
}
```

### Entelechy Cloud

```json
{
  "entelechyApiUrl": "https://api.mindmods.org",
  "entelechyApiToken": "your-api-key"
}
```

### Local daemon (entelechy-embed)

Set an LLM API key and Entelechy will start the local server automatically:

```bash
export OPENAI_API_KEY=sk-your-key
# or
export ANTHROPIC_API_KEY=your-key
```

### Configuration options

| Key | Default | Description |
|-----|---------|-------------|
| `entelechyApiUrl` | `""` | External API URL (empty = local daemon) |
| `entelechyApiToken` | `null` | API token for Entelechy Cloud |
| `bankId` | `"codex"` | Memory bank identifier |
| `bankMission` | (set) | Guides what facts Entelechy retains |
| `autoRecall` | `true` | Inject memories before each prompt |
| `autoRetain` | `true` | Store conversations after each turn |
| `retainMode` | `"full-session"` | `"full-session"` or `"chunked"` |
| `retainEveryNTurns` | `10` | Retain every N turns (1 = every turn) |
| `recallBudget` | `"mid"` | Recall depth: `"low"`, `"mid"`, `"high"` |
| `recallMaxTokens` | `1024` | Max tokens for injected memories |
| `dynamicBankId` | `false` | Separate bank per project/session |
| `dynamicBankGranularity` | `["agent", "project"]` | Fields for dynamic bank ID |
| `debug` | `false` | Log debug info to stderr |

### Environment variable overrides

All settings can also be set via environment variables:

```bash
export ENTELECHY_API_URL=https://api.mindmods.org
export ENTELECHY_API_TOKEN=your-api-key
export ENTELECHY_BANK_ID=my-project
export ENTELECHY_DEBUG=true
```

## How memory works

**Recall** — before each prompt, Entelechy searches your memory bank for facts relevant to what you're about to ask. Found memories are injected as context so Codex has continuity across sessions.

**Retain** — after each turn, Codex's conversation is stored to Entelechy. The memory engine extracts facts, relationships, and experiences — so you don't need to re-explain your stack, preferences, or past decisions.

## Dynamic bank IDs

To keep separate memory per project:

```json
{
  "dynamicBankId": true,
  "dynamicBankGranularity": ["agent", "project"]
}
```

This creates banks like `codex::my-project` automatically, using the working directory name.

## Troubleshooting

**Memory not appearing**: Enable debug mode (`"debug": true`) and check stderr output.

**Server not starting**: Set `entelechyApiUrl` to use an external server, or ensure `uvx` is on PATH for local daemon mode.

**Hooks not firing**: Check that `~/.codex/config.toml` contains `codex_hooks = true` under `[features]`, and that your Codex CLI version supports hooks (v0.116.0+).
