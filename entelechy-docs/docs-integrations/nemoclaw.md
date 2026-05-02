---
sidebar_position: 5
title: "NemoClaw Persistent Memory with Entelechy | Integration Guide"
description: "Add persistent memory to NemoClaw sandboxed agents with Entelechy. One command adds automated memory extraction and auto-recall to any NemoClaw sandbox — no code changes required."
---

# NemoClaw

Persistent memory for [NemoClaw](https://nemoclaw.ai) sandboxed agents using [Entelechy](https://entelechy.vectorize.io).

NemoClaw runs [OpenClaw](https://openclaw.ai) inside an OpenShell sandbox with controlled filesystem, process, and network egress policies. The `entelechy-nemoclaw` package automates adding Entelechy memory to a sandbox in one command — no code changes required.

[View Changelog →](/changelog/integrations/nemoclaw)

## Quick Start

```bash
npx @vectorize-io/entelechy-nemoclaw setup \
  --sandbox my-assistant \
  --api-url https://api.entelechy.vectorize.io \
  --api-token <your-api-key> \
  --bank-prefix my-sandbox
```

Get an API key at [Entelechy Cloud](https://ui.entelechy.vectorize.io/signup).

You'll see output like:

```
[0] Preflight checks...
  ✓ openshell found
  ✓ openclaw found

[1] Installing @vectorize-io/entelechy-openclaw plugin...
  ✓ Plugin installed

[2] Configuring plugin in ~/.openclaw/openclaw.json...
  ✓ Plugin config written (bank: my-sandbox-openclaw)

[3] Applying Entelechy network policy to sandbox "my-assistant"...
  ✓ Policy version 2 submitted
  ✓ Policy version 2 loaded (active version: 2)

[4] Restarting OpenClaw gateway...
  ✓ Gateway restarted

✓ Setup complete!
```

## How It Works

### The sandbox problem

OpenShell enforces strict network egress — every outbound endpoint must be explicitly permitted in the sandbox policy. By default, the Entelechy API (`api.entelechy.vectorize.io`) is not in that list.

The `entelechy-openclaw` plugin supports **external API mode**, where it skips the local daemon entirely and makes direct HTTPS calls to Entelechy Cloud. This is the natural fit for sandboxed environments: the plugin becomes a thin HTTP client, and the only sandbox change needed is one egress rule.

### What the setup command does

1. **Preflight** — verifies `openshell` and `openclaw` are installed
2. **Install plugin** — runs `openclaw plugins install @vectorize-io/entelechy-openclaw`
3. **Configure plugin** — writes external API mode config to `~/.openclaw/openclaw.json`
4. **Apply policy** — reads the current sandbox policy, merges the Entelechy egress block, and re-applies via `openshell policy set`
5. **Restart gateway** — runs `openclaw gateway restart`

### Memory flow

Once set up, the `entelechy-openclaw` plugin hooks into the OpenClaw gateway lifecycle:

- **`before_agent_start`** — recalls relevant memories from past sessions and injects them into context
- **`agent_end`** — retains the conversation to the Entelechy memory bank

The sandbox doesn't interfere with either step — it sees the Entelechy calls as normal HTTPS egress to a permitted endpoint.

## CLI Reference

```
entelechy-nemoclaw setup [options]

Options:
  --sandbox <name>       NemoClaw sandbox name (required)
  --api-url <url>        Entelechy API URL (required)
  --api-token <token>    Entelechy API token (required)
  --bank-prefix <prefix> Memory bank prefix (default: "nemoclaw")
  --skip-policy          Skip sandbox network policy update
  --skip-plugin-install  Skip openclaw plugin installation
  --dry-run              Preview changes without applying
  --help                 Show help
```

Use `--dry-run` to preview all changes before applying anything. Use `--skip-policy` if you manage sandbox policies manually.

## Manual Setup

If you prefer to apply the steps yourself instead of using the CLI:

### 1. Install the plugin

```bash
openclaw plugins install @vectorize-io/entelechy-openclaw
```

### 2. Configure `~/.openclaw/openclaw.json`

```json
{
  "plugins": {
    "entries": {
      "entelechy-openclaw": {
        "enabled": true,
        "config": {
          "entelechyApiUrl": "https://api.entelechy.vectorize.io",
          "entelechyApiToken": "<your-api-key>",
          "llmProvider": "claude-code",
          "dynamicBankId": false,
          "bankIdPrefix": "my-sandbox"
        }
      }
    }
  }
}
```

`llmProvider: "claude-code"` uses the Claude Code process already present in the sandbox — no additional API key needed.

### 3. Add the Entelechy network policy

`openshell policy set` replaces the entire policy document. Export your current policy first, add the Entelechy block, then re-apply:

```yaml
network_policies:
  entelechy:
    name: entelechy
    endpoints:
      - host: api.entelechy.vectorize.io
        port: 443
        protocol: rest
        tls: terminate
        enforcement: enforce
        rules:
          - allow:
              method: GET
              path: /**
          - allow:
              method: POST
              path: /**
          - allow:
              method: PUT
              path: /**
    binaries:
      - path: /usr/local/bin/openclaw
```

```bash
openshell policy set my-sandbox --policy /path/to/full-policy.yaml --wait
openclaw gateway restart
```

## Configuration Options

| Option | Type | Default | Description |
|---|---|---|---|
| `entelechyApiUrl` | string | — | Entelechy API base URL |
| `entelechyApiToken` | string | — | API token for authentication |
| `llmProvider` | string | auto-detect | LLM provider for memory extraction |
| `dynamicBankId` | boolean | `false` | Isolate memory per user (`true`) or share across sessions (`false`) |
| `bankIdPrefix` | string | `"nemoclaw"` | Prefix for the memory bank name |

### Bank naming

When `dynamicBankId: false`, all sessions write to a single bank named `{bankIdPrefix}-openclaw`. When `dynamicBankId: true`, each user gets an isolated bank — useful for multi-tenant deployments.

## Verifying It Works

After setup, check the gateway logs:

```bash
tail -f /tmp/openclaw/openclaw-*.log | grep Entelechy
```

On startup you should see:

```
[Entelechy] Plugin loaded successfully
[Entelechy] ✓ Using external API: https://api.entelechy.vectorize.io
[Entelechy] External API health: {"status":"healthy","database":"connected"}
[Entelechy] Default bank: my-sandbox-openclaw
[Entelechy] ✓ Ready (external API mode)
```

After a conversation:

```
[Entelechy] before_agent_start - bank: my-sandbox-openclaw, channel: undefined/webchat
[Entelechy Hook] agent_end triggered - bank: my-sandbox-openclaw
[Entelechy] Retained 6 messages to bank my-sandbox-openclaw for session agent:main:...
```

## Pitfalls

### Policy replacement is full-document

`openshell policy set` replaces the entire policy document. The `entelechy-nemoclaw setup` command handles this automatically. If you're applying manually, export the current policy first so existing rules aren't lost.

### LaunchAgent can't follow symlinks on macOS

On macOS, the OpenClaw gateway runs as a LaunchAgent under a restricted security context. `openclaw plugins install --link` creates a symlink the LaunchAgent can't follow — the setup command installs as a copy instead. If you see `EPERM: operation not permitted, scandir` in gateway logs, this is the cause.

### Memory retention is asynchronous

Fact extraction and entity resolution happen in the background after `retain`. If you open a new session immediately after closing one, the most recent memories may not be indexed yet — typically a few seconds.

### Binary-scoped egress

The `binaries` field in the network policy restricts the egress rule to a specific executable path. If OpenClaw updates and the binary path changes, the rule silently stops working. Check your binary path after upgrades.

## Troubleshooting

### Plugin not loading

```bash
openclaw plugins list | grep entelechy
# Should show: ✓ enabled │ Entelechy Memory │ ...

# Reinstall
openclaw plugins install @vectorize-io/entelechy-openclaw
```

### Egress blocked

If calls to `api.entelechy.vectorize.io` are being blocked, check the active sandbox policy:

```bash
openshell sandbox get my-assistant
```

Verify the `entelechy` block is present and the `binaries` path matches your OpenClaw binary:

```bash
which openclaw
```

### External API not connecting

```bash
tail -f /tmp/openclaw/openclaw-*.log | grep Entelechy

# If you see daemon startup messages instead of "Using external API",
# the plugin config isn't being read — check ~/.openclaw/openclaw.json
```
