---
sidebar_position: 4
---

# CLI Reference

The Entelechy CLI provides command-line access to memory operations and bank management. All commands follow the [OpenAPI specification](/api-reference), so you can use `--help` on any command to see all available options.

## Installation

```bash
curl -fsSL https://mindmods.org/get-cli | bash
```

## Configuration

Configure the API URL:

```bash
# Interactive configuration
entelechy configure

# Or set directly
entelechy configure --api-url http://localhost:8888

# With API key for authentication
entelechy configure --api-url http://localhost:8888 --api-key your-api-key

# Or use environment variables (highest priority)
export ENTELECHY_API_URL=http://localhost:8888
export ENTELECHY_API_KEY=your-api-key
```

### Named Profiles

When you need to switch between multiple Entelechy deployments (e.g. local,
staging, production) without constantly rewriting `~/.entelechy/config`, use
named profiles. Each profile is a TOML file at
`~/.entelechy/cli-profiles/<name>.toml` and is selected per-invocation with
`-p/--profile` (or by setting `$ENTELECHY_PROFILE`).

```bash
# Create (or overwrite) a profile
entelechy profile create prod \
  --api-url https://api.mindmods.org \
  --api-key hsk_...

# List and inspect profiles
entelechy profile list
entelechy profile show prod

# Use a profile for a single command
entelechy -p prod bank list

# Or make it sticky for the current shell
export ENTELECHY_PROFILE=prod
entelechy bank list

# Remove a profile
entelechy profile delete prod -y
```

Profile files are written with `0600` permissions on Unix so the API key is
only readable by the owner.

**Configuration precedence** (highest first):

1. Environment variables (`ENTELECHY_API_URL`, `ENTELECHY_API_KEY`)
2. Named profile — explicit `-p <name>`, otherwise `$ENTELECHY_PROFILE`
3. Shared config file (`~/.entelechy/config`, written by `entelechy configure`)
4. Default (`http://localhost:8888`)

`ENTELECHY_API_URL` / `ENTELECHY_API_KEY` always override profile values, which
makes it safe to use `-p` in scripts while letting CI inject credentials via
environment.

## Core Commands

### Retain (Store Memory)

Store a single memory:

```bash
entelechy memory retain <bank_id> "Alice works at Google as a software engineer"

# With context
entelechy memory retain <bank_id> "Bob loves hiking" --context "hobby discussion"

# Queue for background processing
entelechy memory retain <bank_id> "Meeting notes" --async
```

### Retain Files

Bulk import from files:

```bash
# Single file
entelechy memory retain-files <bank_id> notes.txt

# Directory (recursive by default)
entelechy memory retain-files <bank_id> ./documents/

# With context
entelechy memory retain-files <bank_id> meeting-notes.txt --context "team meeting"

# Background processing
entelechy memory retain-files <bank_id> ./data/ --async
```

### Recall (Search)

Search memories using semantic similarity:

```bash
entelechy memory recall <bank_id> "What does Alice do?"

# With options
entelechy memory recall <bank_id> "hiking recommendations" \
  --budget high \
  --max-tokens 8192

# Filter by fact type
entelechy memory recall <bank_id> "query" --fact-type world,observation

# Filter by tags
entelechy memory recall <bank_id> "query" --tags work,project \
  --tags-match all

# Pin results to a specific time
entelechy memory recall <bank_id> "query" --query-timestamp "2026-01-15T00:00:00Z"

# Show trace information
entelechy memory recall <bank_id> "query" --trace
```

### Reflect (Generate Response)

Generate a response using memories and bank disposition:

```bash
entelechy memory reflect <bank_id> "What do you know about Alice?"

# With additional context
entelechy memory reflect <bank_id> "Should I learn Python?" --context "career advice"

# Higher budget for complex questions
entelechy memory reflect <bank_id> "Summarize my week" --budget high

# Filter by fact type
entelechy memory reflect <bank_id> "query" \
  --fact-types world,experience \
  --exclude-mental-models
```

### Memory History

View the observation history for a specific memory unit:

```bash
entelechy memory history <bank_id> <memory_id>
```

### Clear Observations

Remove all observations for a memory unit, keeping the core fact:

```bash
entelechy memory clear-observations <bank_id> <memory_id>

# Skip confirmation prompt
entelechy memory clear-observations <bank_id> <memory_id> -y
```

## Bank Management

### List Banks

```bash
entelechy bank list
```

### View Disposition

```bash
entelechy bank disposition <bank_id>
```

### Set Disposition

```bash
entelechy bank set-disposition <bank_id> --mission "..." --name "..."
```

### View Statistics

```bash
entelechy bank stats <bank_id>
```

### Set Bank Name

```bash
entelechy bank name <bank_id> "My Assistant"
```

### Set Mission

```bash
entelechy bank mission <bank_id> "I am a helpful AI assistant interested in technology"
```

### Clear Observations (Bank-wide)

Remove all observations across the entire bank:

```bash
entelechy bank clear-observations <bank_id>

# Skip confirmation prompt
entelechy bank clear-observations <bank_id> -y
```

### Recover Consolidation

Recover from a failed or stuck consolidation:

```bash
entelechy bank consolidation-recover <bank_id>
```

## Document Management

```bash
# List documents
entelechy document list <bank_id>

# Get document details
entelechy document get <bank_id> <document_id>

# Update document metadata
entelechy document update <bank_id> <document_id> --context "updated context"

# Delete document and its memories
entelechy document delete <bank_id> <document_id>
```

## Entity Management

```bash
# List entities
entelechy entity list <bank_id>

# Get entity details
entelechy entity get <bank_id> <entity_id>
```

## Operation Management

Track and manage async operations (retain-files, consolidation, etc.):

```bash
# List operations
entelechy operation list <bank_id>

# Get operation status
entelechy operation get <bank_id> <operation_id>

# Cancel a pending operation
entelechy operation cancel <bank_id> <operation_id>

# Retry a failed operation
entelechy operation retry <bank_id> <operation_id>
```

## Webhook Management

Configure event delivery hooks for bank activity:

```bash
# List webhooks
entelechy webhook list <bank_id>

# Create a webhook (defaults to consolidation.completed events)
entelechy webhook create <bank_id> https://example.com/hook

# Create with specific events and signing secret
entelechy webhook create <bank_id> https://example.com/hook \
  --event-types retain.completed,consolidation.completed \
  --secret my-hmac-secret

# Update a webhook
entelechy webhook update <bank_id> <webhook_id> --url https://new-url.com

# Delete a webhook
entelechy webhook delete <bank_id> <webhook_id>

# View delivery history
entelechy webhook deliveries <bank_id> <webhook_id>
```

## Audit Logs

Inspect the audit trail for a bank:

```bash
# List audit entries
entelechy audit list <bank_id>

# Filter by action and transport
entelechy audit list <bank_id> --action recall --transport mcp

# Filter by date range
entelechy audit list <bank_id> \
  --start-date "2026-04-01T00:00:00Z" \
  --end-date "2026-04-10T00:00:00Z"

# Pagination
entelechy audit list <bank_id> --limit 50 --offset 100
```

## Output Formats

```bash
# Pretty (default)
entelechy memory recall <bank_id> "query"

# JSON
entelechy memory recall <bank_id> "query" -o json

# YAML
entelechy memory recall <bank_id> "query" -o yaml
```

## Global Options

| Flag | Description |
|------|-------------|
| `-v, --verbose` | Show detailed output including request/response |
| `-o, --output <format>` | Output format: pretty, json, yaml |
| `--help` | Show help |
| `--version` | Show version |

## Control Plane UI

Launch the web-based Control Plane UI directly from the CLI:

```bash
entelechy ui
```

This runs the Control Plane locally on port 9999 using the API URL from your configuration. The UI provides:

- **Memory bank management** — Browse and manage all your banks
- **Entity explorer** — Visualize the knowledge graph
- **Query testing** — Interactive recall and reflect testing
- **Operation history** — View ingestion and processing logs

:::tip
The UI command requires Node.js to be installed. It automatically downloads and runs the `@garybense/entelechy-control-plane` package via npx.
:::

## Interactive Explorer

Launch the TUI explorer for visual navigation of your memory banks:

```bash
entelechy explore
```

The explorer provides an interactive terminal interface to:

- **Browse memory banks** — View all banks and their statistics
- **Search memories** — Run recall queries with real-time results
- **Inspect entities** — Explore the knowledge graph and entity relationships
- **View facts** — Browse world facts, experiences, and observations
- **Navigate documents** — See source documents and their extracted memories

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `↑/↓` | Navigate items |
| `Enter` | Select / Expand |
| `Tab` | Switch panels |
| `/` | Search |
| `q` | Quit |

<!-- Screenshot placeholder: explore command TUI -->

## Example Workflow

```bash
# Configure API URL
entelechy configure --api-url http://localhost:8888

# Store some memories
entelechy memory retain demo "Alice works at Google"
entelechy memory retain demo "Bob is a data scientist"
entelechy memory retain demo "Alice and Bob are colleagues"

# Search memories
entelechy memory recall demo "Who works with Alice?"

# Generate a response
entelechy memory reflect demo "What do you know about the team?"

# Check bank disposition
entelechy bank disposition demo
```
