# Installation

Entelechy can be deployed in several ways depending on your infrastructure and requirements.

:::tip Don't want to manage infrastructure?
**[Entelechy Cloud](https://ui.mindmods.org/signup)** is a fully managed service that handles all infrastructure, scaling, and maintenance — [sign up here](https://ui.mindmods.org/signup).
:::

## Prerequisites

### PostgreSQL with pgvector

Entelechy requires PostgreSQL with the **pgvector** extension for vector similarity search.

**By default**, Entelechy uses **pg0** — an embedded PostgreSQL that runs locally on your machine. This is convenient for development but **not recommended for production**.

**For production**, use an external PostgreSQL with pgvector:
- **Supabase** — Managed PostgreSQL with pgvector built-in
- **Neon** — Serverless PostgreSQL with pgvector
- **AWS RDS** / **Cloud SQL** / **Azure** — With pgvector extension enabled
- **Self-hosted** — PostgreSQL 14+ with pgvector installed

### LLM Provider

You need an LLM API key for fact extraction, entity resolution, and answer generation:

- **Groq** (recommended): Fast inference with `gpt-oss-20b`
- **OpenAI**: GPT-4o, GPT-4o-mini
- **Ollama**: Run models locally

See [Models](./models) for detailed comparison and configuration.

---

## Docker

**Best for**: Quick start, development, small deployments

Run everything in one container with embedded PostgreSQL:

```bash
export OPENAI_API_KEY=sk-xxx

docker run --rm -it --pull always -p 8888:8888 -p 9999:9999 \
  -e ENTELECHY_API_LLM_API_KEY=$OPENAI_API_KEY \
  -v $HOME/.entelechy-docker:/home/entelechy/.pg0 \
  ghcr.io/garybense/entelechy:latest
```

- **API Server**: http://localhost:8888
- **Control Plane** (Web UI): http://localhost:9999

---

## Helm / Kubernetes

**Best for**: Production deployments, auto-scaling, cloud environments

```bash
# Install with built-in PostgreSQL
helm install entelechy oci://ghcr.io/garybense/charts/entelechy \
  --set api.llm.provider=groq \
  --set api.llm.apiKey=gsk_xxxxxxxxxxxx \
  --set postgresql.enabled=true

# Or use external PostgreSQL
helm install entelechy oci://ghcr.io/garybense/charts/entelechy \
  --set api.llm.provider=groq \
  --set api.llm.apiKey=gsk_xxxxxxxxxxxx \
  --set postgresql.enabled=false \
  --set api.database.url=postgresql://user:pass@postgres.example.com:5432/entelechy

# Install a specific version
helm install entelechy oci://ghcr.io/garybense/charts/entelechy --version 0.1.3

# Upgrade to latest
helm upgrade entelechy oci://ghcr.io/garybense/charts/entelechy
```

**Requirements**:
- Kubernetes cluster (GKE, EKS, AKS, or self-hosted)
- Helm 3.8+

### Distributed Workers

For high-throughput deployments, enable dedicated worker pods to scale task processing independently:

```bash
helm install entelechy oci://ghcr.io/garybense/charts/entelechy \
  --set worker.enabled=true \
  --set worker.replicaCount=3
```

See [Services - Worker Service](./services#worker-service) for configuration details and architecture.

See the [Helm chart values.yaml](https://github.com/garybense/entelechy/tree/main/helm/entelechy/values.yaml) for all chart options.

---

## Bare Metal (pip)

**Best for**: Custom deployments, integration into existing Python applications

### Install

```bash
pip install entelechy-all
```

### Run with Embedded Database

For development and testing, Entelechy can run with an embedded PostgreSQL (pg0):

```bash
export ENTELECHY_API_LLM_PROVIDER=groq
export ENTELECHY_API_LLM_API_KEY=gsk_xxxxxxxxxxxx

entelechy-api
```

This creates a database in `~/.entelechy/data/` and starts the API on http://localhost:8888.

### Run with External PostgreSQL

For production, connect to your own PostgreSQL instance:

```bash
export ENTELECHY_API_DATABASE_URL=postgresql://user:pass@localhost:5432/entelechy
export ENTELECHY_API_LLM_PROVIDER=groq
export ENTELECHY_API_LLM_API_KEY=gsk_xxxxxxxxxxxx

entelechy-api
```

**Note**: The database must exist and have pgvector enabled (`CREATE EXTENSION vector;`).

### CLI Options

```bash
entelechy-api --port 9000          # Custom port (default: 8888)
entelechy-api --host 127.0.0.1     # Bind to localhost only
entelechy-api --workers 4          # Multiple worker processes
entelechy-api --log-level debug    # Verbose logging
```

### Control Plane

The Control Plane (Web UI) can be run standalone using npx:

```bash
npx @garybense/entelechy-control-plane --api-url http://localhost:8888
```

This connects to your running API server and provides a visual interface for managing memory banks, exploring entities, and testing queries.

#### Options

| Option | Environment Variable | Default | Description |
|--------|---------------------|---------|-------------|
| `-p, --port` | `PORT` | 9999 | Port to listen on |
| `-H, --hostname` | `HOSTNAME` | 0.0.0.0 | Hostname to bind to |
| `-a, --api-url` | `ENTELECHY_CP_DATAPLANE_API_URL` | http://localhost:8888 | Entelechy API URL |

#### Examples

```bash
# Run on custom port
npx @garybense/entelechy-control-plane --port 9999 --api-url http://localhost:8888

# Using environment variables
export ENTELECHY_CP_DATAPLANE_API_URL=http://api.example.com
npx @garybense/entelechy-control-plane

# Production deployment
PORT=80 ENTELECHY_CP_DATAPLANE_API_URL=https://api.entelechy.io npx @garybense/entelechy-control-plane
```

---

## Next Steps

- [Configuration](./configuration.md) — Environment variables and settings
- [Models](./models.md) — ML models and providers
- [Monitoring](./monitoring.md) — Metrics and observability
