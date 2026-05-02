# @vectorize-io/entelechy-paperclip

Persistent long-term memory for Paperclip agents via [Entelechy](https://github.com/vectorize-io/entelechy).

Install once. Every agent in your Paperclip instance gets memory that persists across runs, companies, and restarts.

## What It Does

- **Before each run** — recalls relevant memories from past runs and caches them for the agent
- **After each run** — retains the agent's output to Entelechy automatically
- **Agent tools** — `entelechy_recall` and `entelechy_retain` tools for agents to query and store memory mid-run

## Installation

```bash
pnpm paperclipai plugin install @vectorize-io/entelechy-paperclip
```

Then configure in **Settings → Plugins → Entelechy Memory**.

## Prerequisites

Either:

```bash
# Self-hosted (runs locally)
pip install entelechy-all
export ENTELECHY_API_LLM_API_KEY=your-openai-key
entelechy-api
```

Or [Entelechy Cloud](https://ui.entelechy.vectorize.io/signup) — no self-hosting required.

## Configuration

| Field                | Default                 | Description                                                    |
| -------------------- | ----------------------- | -------------------------------------------------------------- |
| `entelechyApiUrl`    | `http://localhost:8888` | Entelechy server URL                                           |
| `entelechyApiKeyRef` | —                       | Paperclip secret name holding Entelechy Cloud API key          |
| `bankGranularity`    | `["company", "agent"]`  | Memory isolation: per company+agent, per company, or per agent |
| `recallBudget`       | `mid`                   | `low` = fastest, `mid` = balanced, `high` = most thorough      |
| `autoRetain`         | `true`                  | Automatically retain run output after every run                |

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

## How It Works

```
agent.run.started
  └─ recall(issueTitle + description)
       └─ store in plugin state for this run (instant lookup by tools)

agent running…
  ├─ entelechy_recall(query) → returns cached context or live recall
  └─ entelechy_retain(content) → stores immediately

agent.run.finished
  └─ retain(output) → stored in Entelechy with runId as document_id
```

Memory is keyed to `companyId` + `agentId`, never to the Paperclip session or run ID — so it survives across any number of runs.

## Development

```bash
npm install
npm run build
npm test
```

Local install into a running Paperclip instance:

```bash
curl -X POST http://127.0.0.1:3100/api/plugins/install \
  -H "Content-Type: application/json" \
  -d '{"packageName":"/absolute/path/to/entelechy-integrations/paperclip","isLocalPath":true}'
```
