# entelechy-embed

Entelechy embedded CLI - local memory operations with automatic daemon management.

This package provides a simple CLI for storing and recalling memories using Entelechy's memory engine. It automatically manages a background daemon for fast operations - no manual server setup required.

## How It Works

`entelechy-embed` uses a background daemon architecture for optimal performance:

1. **First command**: Automatically starts a local daemon (first run downloads dependencies and loads ML models - can take 1-3 minutes)
2. **Subsequent commands**: Near-instant responses (~1-2s) since daemon is already running
3. **Auto-shutdown**: Daemon automatically exits after 5 minutes of inactivity

The daemon runs on `localhost:8888` and uses an embedded PostgreSQL database (pg0) - everything stays local on your machine.

## Installation

```bash
pip install entelechy-embed
# or with uvx (no install needed)
uvx entelechy-embed --help
```

## Quick Start

```bash
# Interactive setup (configures default profile)
entelechy-embed configure

# Or set your LLM API key manually
export OPENAI_API_KEY=sk-...

# Store a memory (bank_id = "default")
entelechy-embed memory retain default "User prefers dark mode"

# Recall memories
entelechy-embed memory recall default "What are user preferences?"
```

All commands use the "default" profile unless you specify a different one with `--profile` or `ENTELECHY_EMBED_PROFILE`.

## Commands

### configure

Configure the default profile or create/update named profiles:

```bash
# Interactive setup for default profile
entelechy-embed configure

# Create/update named profile with single command
entelechy-embed configure --profile my-app \
  --env ENTELECHY_EMBED_LLM_PROVIDER=openai \
  --env ENTELECHY_EMBED_LLM_API_KEY=sk-xxx

# Create/update named profile interactively
entelechy-embed configure --profile staging
```

This will:
- Let you choose an LLM provider (OpenAI, Groq, Google, Ollama)
- Configure your API key
- Set the model and memory bank ID
- Start the daemon with your configuration

### memory retain

Store a memory:

```bash
entelechy-embed memory retain default "User prefers dark mode"
entelechy-embed memory retain default "Meeting on Monday" --context work
entelechy-embed memory retain myproject "API uses JWT authentication"
```

### memory recall

Search memories:

```bash
entelechy-embed memory recall default "user preferences"
entelechy-embed memory recall default "upcoming events"
```

Use `-o json` for JSON output:
```bash
entelechy-embed memory recall default "user preferences" -o json
```

### memory reflect

Get contextual answers that synthesize multiple memories:

```bash
entelechy-embed memory reflect default "How should I set up the dev environment?"
```

### bank list

List all memory banks:

```bash
entelechy-embed bank list
```

### profile

Manage configuration profiles:

```bash
# List all profiles with status
entelechy-embed profile list

# Show current active profile
entelechy-embed profile show

# Set active profile (persists across commands)
entelechy-embed profile set-active my-app

# Clear active profile (revert to default)
entelechy-embed profile set-active --none

# Delete a profile
entelechy-embed profile delete my-app
```

### daemon

Manage the background daemon:

```bash
entelechy-embed daemon status    # Check if daemon is running
entelechy-embed daemon start     # Start the daemon
entelechy-embed daemon stop      # Stop the daemon
entelechy-embed daemon logs      # View last 50 lines of logs
entelechy-embed daemon logs -f   # Follow logs in real-time
entelechy-embed daemon logs -n 100  # View last 100 lines
```

## Configuration

### Interactive Setup

Run `entelechy-embed configure` for a guided setup that saves to `~/.entelechy/embed`.

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ENTELECHY_EMBED_PROFILE` | Profile name to use (overrides active profile) | None (uses default profile) |
| `ENTELECHY_EMBED_LLM_API_KEY` | LLM API key (or use `OPENAI_API_KEY`) | Required |
| `ENTELECHY_EMBED_LLM_PROVIDER` | LLM provider (`openai`, `groq`, `google`, `ollama`) | `openai` |
| `ENTELECHY_EMBED_LLM_MODEL` | LLM model | `gpt-4o-mini` |
| `ENTELECHY_EMBED_BANK_ID` | Default memory bank ID (optional, used when not specified in CLI) | `default` |
| `ENTELECHY_EMBED_API_URL` | Use external API server instead of starting local daemon | None (starts local daemon) |
| `ENTELECHY_EMBED_API_TOKEN` | Authentication token for external API (sent as Bearer token) | None |
| `ENTELECHY_EMBED_API_DATABASE_URL` | Database URL for daemon | `pg0://entelechy-embed` |
| `ENTELECHY_EMBED_DAEMON_IDLE_TIMEOUT` | Seconds before daemon auto-exits when idle | `300` |

**Using an External API Server:**

To connect to an existing Entelechy API server instead of starting the local daemon:

```bash
export ENTELECHY_EMBED_API_URL=http://your-server:8000
export ENTELECHY_EMBED_API_TOKEN=your-api-token  # Optional, if API requires auth
entelechy-embed memory recall default "query"
```

**Custom Database:**

To use an external PostgreSQL database instead of the embedded pg0 database (useful when running as root or in containerized environments):

```bash
export ENTELECHY_EMBED_API_DATABASE_URL=postgresql://user:password@localhost:5432/dbname
entelechy-embed daemon start
```

**Note:** All banks share a single database. Bank isolation happens within the database via the `bank_id` parameter passed to CLI commands.

### Configuration Profiles

Profiles let you maintain multiple independent configurations (e.g., different API endpoints, LLM providers, or projects). Each profile runs its own daemon on a unique port (8889-9888).

**The Default Profile:**

When you run `entelechy-embed configure` without specifying a profile, it configures the "default" profile. This uses the backward-compatible configuration at `~/.entelechy/embed` and runs on port 8888.

**Creating Named Profiles:**

```bash
# Create a profile with single command
entelechy-embed configure --profile my-app \
  --env ENTELECHY_EMBED_LLM_PROVIDER=openai \
  --env ENTELECHY_EMBED_LLM_API_KEY=sk-xxx \
  --env ENTELECHY_EMBED_LLM_MODEL=gpt-4o-mini

# Create a profile interactively
entelechy-embed configure --profile staging
```

**Using Profiles:**

```bash
# Option 1: Environment variable (recommended for apps)
ENTELECHY_EMBED_PROFILE=my-app entelechy-embed memory retain default "text"

# Option 2: CLI flag
entelechy-embed --profile my-app memory recall default "query"

# Option 3: Set as active (persists across commands)
entelechy-embed profile set-active my-app
entelechy-embed memory recall default "query"  # Uses my-app profile

# Clear active profile (revert to default)
entelechy-embed profile set-active --none
```

**Profile Management:**

```bash
# List all profiles with status
entelechy-embed profile list

# Show active profile
entelechy-embed profile show

# Delete a profile
entelechy-embed profile delete my-app
```

**Profile Resolution Priority:**
1. `ENTELECHY_EMBED_PROFILE` environment variable (highest)
2. `--profile` CLI flag
3. Active profile from `~/.entelechy/active_profile` file
4. Default profile (lowest)

**Note:** If a profile is specified but doesn't exist, the command will fail with an error. Profiles must be explicitly created using `entelechy-embed configure --profile <name>`.

### Files

**Default Profile:**
| Path | Description |
|------|-------------|
| `~/.entelechy/embed` | Configuration file for default profile |
| `~/.entelechy/daemon.log` | Daemon logs for default profile |
| `~/.entelechy/daemon.lock` | Daemon lock file (PID) for default profile |

**Named Profiles:**
| Path | Description |
|------|-------------|
| `~/.entelechy/profiles/<name>.env` | Configuration file for profile |
| `~/.entelechy/profiles/<name>.log` | Daemon logs for profile |
| `~/.entelechy/profiles/<name>.lock` | Daemon lock file (PID) for profile |
| `~/.entelechy/profiles/metadata.json` | Profile metadata (ports, timestamps) |
| `~/.entelechy/active_profile` | Active profile name (when set with `profile set-active`) |

## Use with AI Coding Assistants

This CLI is designed to work with AI coding assistants like Claude Code, Cursor, and Windsurf. Install the Entelechy skill:

```bash
curl -fsSL https://mindmods.org/get-skill | bash
```

This will configure the LLM provider and install the skill to your assistant's skills directory.

## Troubleshooting

**Daemon won't start:**
```bash
# Check logs for errors
entelechy-embed daemon logs

# Stop any stuck daemon and restart
entelechy-embed daemon stop
entelechy-embed daemon start
```

**Slow first command:**
This is expected - the first command needs to download dependencies, start the daemon, and load ML models. First run can take 1-3 minutes depending on network speed. Subsequent commands will be fast (~1-2s).

**Change configuration:**
```bash
# Re-run configure (automatically restarts daemon)
entelechy-embed configure
```

## License

Apache 2.0
