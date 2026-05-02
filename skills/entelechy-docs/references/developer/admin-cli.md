# Admin CLI

The `entelechy-admin` CLI provides administrative commands for managing your Entelechy deployment, including database migrations, backup, and restore operations.

## Installation

The admin CLI is included with the `entelechy-api` package:

```bash
pip install entelechy-api
# or
uv add entelechy-api
```

## Commands

### run-db-migration

Run database migrations to the latest version. By default this migrates the base schema plus all tenant schemas discovered by the tenant extension. Use `--schema` for targeted migration of one schema. This is useful when you want to run migrations separately from API startup (e.g., in CI/CD pipelines or before deploying a new version).

```bash
entelechy-admin run-db-migration [OPTIONS]
```

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--schema`, `-s` | Database schema to run migrations on. If omitted, migrate the base schema plus all discovered tenant schemas. | All schemas |

**Examples:**

```bash
# Run migrations on the base schema plus all discovered tenant schemas
entelechy-admin run-db-migration

# Run migrations on a specific tenant schema
entelechy-admin run-db-migration --schema tenant_acme
```

:::tip Disabling Auto-Migrations
To disable automatic migrations on API startup, set `ENTELECHY_API_RUN_MIGRATIONS_ON_STARTUP=false`. This is useful when you want to run migrations as a separate step in your deployment pipeline.
:::

---

### backup

Create a backup of all Entelechy data to a zip file.

```bash
entelechy-admin backup OUTPUT [OPTIONS]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `OUTPUT` | Output file path (will add `.zip` extension if not present) |

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--schema`, `-s` | Database schema to backup | `public` |

**Examples:**

```bash
# Backup to a file
entelechy-admin backup /backups/entelechy-2024-01-15.zip

# Backup a specific tenant schema
entelechy-admin backup /backups/tenant-acme.zip --schema tenant_acme
```

The backup includes:
- Memory banks and their configuration
- Documents and chunks
- Entities and their relationships
- Memory units (facts, experiences, observations)
- Entity cooccurrences and memory links

:::note Consistency
Backups are created within a database transaction with `REPEATABLE READ` isolation, ensuring a consistent snapshot across all tables.
:::

---

### restore

Restore data from a backup file. **Warning: This deletes all existing data in the target schema.**

```bash
entelechy-admin restore INPUT [OPTIONS]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `INPUT` | Input backup file (.zip) |

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--schema`, `-s` | Database schema to restore to | `public` |
| `--yes`, `-y` | Skip confirmation prompt | `false` |

**Examples:**

```bash
# Restore with confirmation prompt
entelechy-admin restore /backups/entelechy-2024-01-15.zip

# Restore without confirmation (for scripts)
entelechy-admin restore /backups/entelechy-2024-01-15.zip --yes

# Restore to a specific tenant schema
entelechy-admin restore /backups/tenant-acme.zip --schema tenant_acme --yes
```

:::warning Data Loss
Restore will **delete all existing data** in the target schema before importing the backup. Always verify you have a recent backup before performing a restore.
:::

---

### decommission-worker

Release all tasks owned by a worker, resetting them from "processing" back to "pending" status so they can be picked up by other workers.

```bash
entelechy-admin decommission-worker WORKER_ID [OPTIONS]
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `WORKER_ID` | ID of the worker to decommission |

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--schema`, `-s` | Database schema | `public` |

**Examples:**

```bash
# Before scaling down - release tasks from workers being removed
entelechy-admin decommission-worker entelechy-worker-4
entelechy-admin decommission-worker entelechy-worker-3

# Release tasks from a crashed worker
entelechy-admin decommission-worker worker-2

# For a specific tenant schema
entelechy-admin decommission-worker worker-1 --schema tenant_acme
```

**When to Use:**

- **Scaling down**: Before removing worker replicas in Kubernetes
- **Graceful removal**: When taking a worker offline for maintenance
- **Crash recovery**: If a worker crashed while processing tasks
- **Stuck worker**: When a worker is unresponsive

:::tip Finding Worker IDs
Worker IDs default to the hostname. In Kubernetes StatefulSets, this is the pod name (e.g., `entelechy-worker-0`). You can also set a custom ID with `ENTELECHY_API_WORKER_ID` or `--worker-id`.
:::


### decommission-workers

Release all currently-processing tasks from every worker, resetting them from "processing" back to "pending" status. Use this when one or more workers have crashed or been removed without graceful shutdown and you don't know which worker IDs to target.

```bash
entelechy-admin decommission-workers [OPTIONS]
```

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--schema`, `-s` | Database schema | `public` |
| `--yes`, `-y` | Skip confirmation prompt | `false` |

**Examples:**

```bash
# Release all processing tasks across all workers (with confirmation)
entelechy-admin decommission-workers

# Skip the confirmation prompt (useful in scripts)
entelechy-admin decommission-workers --yes

# Release tasks in a specific tenant schema
entelechy-admin decommission-workers --schema tenant_acme
```

**When to Use:**

- **Unknown dead workers**: Multiple workers crashed and you do not know their IDs
- **Fleet-wide recovery**: After an infrastructure event where many workers went down
- **"Just fix everything"**: A quick full-queue drain when per-worker cleanup is overkill

:::warning Disruptive
This releases **every** processing task regardless of worker, including tasks owned by healthy workers. Prefer `decommission-worker <WORKER_ID>` when you know which workers need cleanup.
:::

---

### worker-status

Show all currently-processing tasks grouped by worker, including operation type, bank, how long each task has been running, and when it was last updated. Useful for identifying orphaned tasks before decommissioning.

```bash
entelechy-admin worker-status [OPTIONS]
```

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--schema`, `-s` | Database schema | `public` |

**Examples:**

```bash
# Show all processing tasks across all workers
entelechy-admin worker-status

# Show processing tasks for a specific tenant schema
entelechy-admin worker-status --schema tenant_acme
```

**When to Use:**

- **Before decommissioning**: Inspect which workers have stale tasks and how long they have been stuck
- **Debugging throughput**: Diagnose why the queue is not draining (are tasks stuck in processing?)
- **Worker health check**: Spot workers whose `last_update_ago` keeps growing, indicating a dead or unresponsive worker

---

## Environment Variables

The admin CLI uses the same environment variables as the API service. The most important one is:

| Variable | Description | Default |
|----------|-------------|---------|
| `ENTELECHY_API_DATABASE_URL` | PostgreSQL connection string | `pg0` (embedded) |

**Example:**

```bash
# Use a specific database
export ENTELECHY_API_DATABASE_URL=postgresql://user:pass@localhost:5432/entelechy
entelechy-admin backup /backups/mybackup.zip
```
