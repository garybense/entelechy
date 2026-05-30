---
sidebar_position: 11
title: "Paperclip Persistent Memory with Entelechy | Integration Guide"
description: "Add long-term memory to all Paperclip agents with Entelechy. Install once as a plugin — every agent gets automatic recall before runs and retain after runs."
---

# Paperclip

Persistent memory for [Paperclip AI](https://github.com/paperclipai/paperclip) agents using [Entelechy](https://mindmods.org).

Install the `@garybense/entelechy-paperclip` plugin once. Every agent in your Paperclip instance automatically gets long-term memory that persists across runs, companies, and restarts — no code changes required.

## Installation

```bash
pnpm paperclipai plugin install @garybense/entelechy-paperclip
```

Then configure in **Settings → Plugins → Entelechy Memory**.

## Prerequisites

Either:

```bash
# Self-hosted
pip install entelechy-all
export ENTELECHY_API_LLM_API_KEY=your-openai-key
entelechy-api
```

Or [Entelechy Cloud](https://ui.mindmods.org/signup) — no self-hosting required.

## How It Works

```
agent.run.started
  └─ recall(issueTitle + description)
       └─ cached in plugin state for this run

agent running…
  ├─ entelechy_recall(query) → returns cached context or live recall
  └─ entelechy_retain(content) → stores immediately

agent.run.finished
  └─ retain(output) → stored with runId as document_id
```

Memory is keyed to `companyId` + `agentId` — never to the run ID — so it accumulates across every run.

## Configuration

| Field | Default | Description |
|-------|---------|-------------|
| `entelechyApiUrl` | `http://localhost:8888` | Entelechy server URL |
| `entelechyApiKeyRef` | — | Paperclip secret name holding Entelechy Cloud API key |
| `bankGranularity` | `["company", "agent"]` | Memory isolation: per company+agent, per company, or per agent |
| `recallBudget` | `mid` | `low` = fastest, `mid` = balanced, `high` = most thorough |
| `autoRetain` | `true` | Automatically retain run output after every run |

## Bank ID Format

```
paperclip::{companyId}::{agentId}    ← default (company + agent granularity)
paperclip::{companyId}               ← company granularity (shared across agents)
paperclip::{agentId}                 ← agent granularity (agent memory across companies)
```

## Agent Tools

Agents can call these tools directly during a run:

**`entelechy_recall(query)`** — search memory for relevant context. Called automatically at run start; agents can also call it mid-run for targeted queries.

**`entelechy_retain(content)`** — store a fact or decision immediately, without waiting for run end.

## Adapter Compatibility

Works with all Paperclip adapter types via the event system:

| Adapter | Supported |
|---------|-----------|
| Claude | ✓ |
| Codex | ✓ |
| Cursor | ✓ |
| HTTP | ✓ |
| Process | ✓ |
