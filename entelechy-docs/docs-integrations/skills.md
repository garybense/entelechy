---
sidebar_position: 3
title: "Entelechy Agent Memory Skill | AI Coding Assistant Integration"
description: "Give AI coding assistants like Claude Code and Codex persistent memory across sessions with Entelechy's Agent Skill — a reusable prompt template for long-term context retention."
---

# Skills

Entelechy provides an Agent Skill that gives AI coding assistants persistent memory across sessions. Skills are reusable prompt templates that agents can load when needed to gain specialized capabilities.

## Supported Platforms

| Platform | Skills Directory |
|----------|-----------------|
| [Claude Code](https://docs.anthropic.com/en/docs/claude-code) | `~/.claude/skills/` |
| [OpenCode](https://github.com/opencode-ai/opencode) | `~/.opencode/skills/` |
| [Codex CLI](https://github.com/openai/codex) | `~/.codex/skills/` |

## Deployment Modes

The skill supports two deployment modes:

| Mode | Best For | Data Location |
|------|----------|---------------|
| **Local** | Individual developers | Your machine (`~/.pg0/`) |
| **Cloud** | Teams sharing knowledge | Entelechy Cloud |

## Quick Install

### Option 1: Interactive Installer (Recommended)

```bash
curl -fsSL https://entelechy.vectorize.io/get-skill | bash
```

The installer will:
1. Prompt you to select your AI coding assistant
2. Select deployment mode (local or cloud)
3. Configure the appropriate settings
4. Install the skill to the appropriate directory

### Install for a Specific Platform

```bash
# Claude Code (interactive mode selection)
curl -fsSL https://entelechy.vectorize.io/get-skill | bash -s -- --app claude

# OpenCode
curl -fsSL https://entelechy.vectorize.io/get-skill | bash -s -- --app opencode

# Codex CLI
curl -fsSL https://entelechy.vectorize.io/get-skill | bash -s -- --app codex
```

### Install with Cloud Mode

```bash
# Direct cloud setup (skips interactive prompts for mode)
curl -fsSL https://entelechy.vectorize.io/get-skill | bash -s -- --app claude --mode cloud
```

### Option 2: Using add-skill

If you use [add-skill](https://add-skill.org/) to manage your agent skills:

```bash
# For local mode (individual developers)
npx add-skill vectorize-io/entelechy --skill entelechy-local

# For Entelechy Cloud (teams)
npx add-skill vectorize-io/entelechy --skill entelechy-cloud

# For self-hosted Entelechy servers
npx add-skill vectorize-io/entelechy --skill entelechy-self-hosted
```

On first use, the AI will guide you through the remaining setup:
- **Local**: Run `uvx entelechy-embed configure` to set up your LLM provider
- **Cloud**: Provide your API key and bank ID
- **Self-hosted**: Provide your server URL, API key, and bank ID

## What the Skill Provides

Once installed, your AI assistant gains the ability to:

- **Retain** - Store user preferences, learnings, and procedure outcomes
- **Recall** - Search for relevant context before starting tasks
- **Reflect** - Synthesize memories into contextual answers

The skill uses the `entelechy-embed` CLI which runs a lightweight local daemon with an embedded database.

## How Skills Work

Skills are **model-invoked**, meaning the AI assistant automatically decides when to use them based on the context of your conversation. You don't need to explicitly trigger the skill.

The assistant will:
- **Store** when you share preferences, when tasks succeed/fail, or when learnings emerge
- **Recall** before starting non-trivial tasks to get relevant context

### What Gets Stored

The skill is optimized to store:

| Category | Examples |
|----------|----------|
| **User Preferences** | Coding style, tool preferences, language choices |
| **Procedure Outcomes** | Commands that worked, configurations that resolved issues |
| **Learnings** | Bug solutions, workarounds, architecture decisions |

## Architecture

### Local Mode

```
AI Coding Assistant
    │
    ▼
Entelechy Skill (SKILL.md)
    │
    ▼
entelechy-embed CLI
    │
    ▼
Local Daemon (auto-started)
    │
    ▼
Embedded PostgreSQL (~/.pg0/entelechy-embed/)
```

All data stays on your machine. The daemon auto-starts when needed and shuts down after inactivity.

### Cloud Mode

```
AI Coding Assistant
    │
    ▼
Entelechy Skill (SKILL.md)
    │
    ▼
entelechy-cli
    │
    ▼
Entelechy Cloud API (https://api.entelechy.vectorize.io)
    │
    ▼
Shared Memory Bank (team-accessible)
```

Data is stored in Entelechy Cloud and shared across your team. All team members with the same bank ID can access shared memories.

---

## Local Mode Setup

The skill uses configuration stored in `~/.entelechy/config.env`. Reconfigure anytime:

```bash
uvx entelechy-embed configure
```

---

## Cloud Mode Setup

Cloud mode connects to [Entelechy Cloud](https://ui.entelechy.vectorize.io/signup), allowing teams to share memories about a codebase. When one team member learns something, everyone benefits.

### Prerequisites

1. A Entelechy Cloud account ([sign up](https://ui.entelechy.vectorize.io/signup))
2. An API key from your team admin
3. A bank ID for your project (e.g., `team-acme-frontend`)

### Installation

Run the installer with cloud mode:

```bash
curl -fsSL https://entelechy.vectorize.io/get-skill | bash -s -- --mode cloud
```

You'll be prompted for:

| Setting | Description | Example |
|---------|-------------|---------|
| **Cloud API URL** | Entelechy Cloud endpoint | `https://api.entelechy.vectorize.io` |
| **API Key** | Your authentication key | `hs_xxx...` |
| **Bank ID** | Shared memory bank for your team | `team-acme-frontend` |

### Configuration Files

Cloud mode creates two files:

**`~/.entelechy/config`** — API connection settings (TOML format):
```toml
api_url = "https://api.entelechy.vectorize.io"
api_key = "hs_xxx..."
```

**`~/.claude/skills/entelechy/SKILL.md`** — Skill definition with your bank ID baked in.

### Team Setup

To set up cloud mode for your team:

1. **Team admin** creates a bank in Entelechy Cloud (e.g., `team-acme-frontend`)
2. **Team admin** generates API keys for each team member
3. **Each developer** runs the installer with their API key and the shared bank ID
4. All team members now share the same memory bank

### What to Store in Team Banks

Cloud mode uses a **shared team bank**. Be thoughtful about what goes in:

| Type | Examples | How to Store |
|------|----------|--------------|
| **Project conventions** | Linting rules, testing requirements, Node version | `"Project uses ESLint with Airbnb config"` |
| **Team knowledge** | Architecture decisions, common pitfalls, domain logic | `"Auth module requires Redis 7+"` |
| **Individual preferences** | Personal coding style, communication preferences | `"Alice prefers verbose commit messages"` |

**Key distinction**: Project conventions apply to everyone. Individual preferences should include the person's name so the AI knows when to apply them.

### Example Workflow

```
Day 1: Alice discovers a requirement
─────────────────────────────────────
Alice's AI assistant stores:
  "The auth module requires Redis 7+ due to HEXPIRE command usage"
  "Alice prefers explicit error handling over silent failures"

Day 2: Bob starts working on auth
─────────────────────────────────
Bob's AI assistant recalls:
  "The auth module requires Redis 7+ due to HEXPIRE command usage"

Bob avoids the same issue Alice hit!
(Alice's personal preference is stored but won't be applied to Bob)
```

### Testing Cloud Connection

After installation, verify the connection:

```bash
# Store a test memory
entelechy memory retain team-acme-frontend "Alice works at Google as a software engineer"

# Recall it
entelechy memory recall team-acme-frontend "Alice"
```

### Switching Between Banks

If you work on multiple projects, you can have different skills installed for each AI assistant, or manually switch banks:

```bash
# Environment variable override (temporary)
ENTELECHY_API_URL=https://api.entelechy.vectorize.io \
ENTELECHY_API_KEY=hs_xxx \
entelechy memory recall different-bank "query"
```

For permanent multi-bank setups, reinstall the skill with a different bank ID.

## Troubleshooting

### Skill not activating

The skill activates based on its description matching your request. Try being explicit:
- "Remember that..." triggers storage
- "What do you know about..." triggers recall

### Local Mode Issues

**Daemon not starting:**
```bash
uvx entelechy-embed daemon status
uvx entelechy-embed daemon logs
```

**Reconfigure LLM provider:**
```bash
uvx entelechy-embed configure
```

### Cloud Mode Issues

**Authentication errors:**
```bash
# Verify your config
cat ~/.entelechy/config

# Test connection manually
entelechy bank list
```

**Wrong bank ID:**

Check your SKILL.md file to see which bank ID is configured:
```bash
cat ~/.claude/skills/entelechy/SKILL.md | grep "memory retain"
```

To change the bank ID, reinstall the skill:
```bash
curl -fsSL https://entelechy.vectorize.io/get-skill | bash -s -- --mode cloud
```

**Network/firewall issues:**
```bash
# Test connectivity to cloud API
curl -I https://api.entelechy.vectorize.io/health
```

## Requirements

### Local Mode
- Python 3.10+ (for `uvx`)
- An LLM API key (OpenAI, Anthropic, Groq, etc.)

### Cloud Mode
- Python 3.10+ (for `uvx`)
- Entelechy Cloud API key
- Network access to `https://api.entelechy.vectorize.io`
