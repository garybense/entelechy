# Entelechy Helm Chart

Helm chart for deploying Entelechy - a temporal-semantic-entity memory system for AI agents.

## Prerequisites

- Kubernetes 1.19+
- Helm 3.0+
- PostgreSQL database (external or bundled)

## Quick Start

```bash
# Update dependencies first
helm dependency update ./helm/entelechy

# Install (PostgreSQL included by default)
export OPENAI_API_KEY="sk-your-openai-key"
helm upgrade entelechy --install ./helm/entelechy -n entelechy --create-namespace \
  --set api.secrets.ENTELECHY_API_LLM_API_KEY="$OPENAI_API_KEY"
```

To use an external database instead:

```bash
helm install entelechy ./helm/entelechy -n entelechy --create-namespace \
  --set api.secrets.ENTELECHY_API_LLM_API_KEY="sk-your-openai-key" \
  --set postgresql.enabled=false \
  --set postgresql.external.host=my-postgres.example.com \
  --set postgresql.external.password=mypassword
```

## Installation

### Add the repository (if published)

```bash
helm repo add entelechy https://your-helm-repo.com
helm repo update
```

### Install with custom values file

Create a `values-override.yaml`:

```yaml
api:
  secrets:
    ENTELECHY_API_LLM_API_KEY: "sk-your-openai-key"

postgresql:
  external:
    host: "my-postgres.example.com"
    password: "mypassword"
```

Then install:

```bash
helm install entelechy ./helm/entelechy -n entelechy --create-namespace -f values-override.yaml
```

## Configuration

### Key Values

| Parameter | Description | Default |
|-----------|-------------|---------|
| `version` | Default image tag for all components | `0.1.0` |
| `api.enabled` | Enable the API component | `true` |
| `api.image.repository` | API image repository | `entelechy/api` |
| `api.image.tag` | API image tag (defaults to `version`) | - |
| `api.service.port` | API service port | `8888` |
| `controlPlane.enabled` | Enable the control plane | `true` |
| `controlPlane.image.repository` | Control plane image repository | `entelechy/control-plane` |
| `controlPlane.image.tag` | Control plane image tag (defaults to `version`) | - |
| `controlPlane.service.port` | Control plane service port | `3000` |
| `postgresql.enabled` | Deploy PostgreSQL as subchart | `true` |
| `postgresql.external.host` | External PostgreSQL host | `postgresql` |
| `postgresql.external.port` | External PostgreSQL port | `5432` |
| `postgresql.external.database` | Database name | `entelechy` |
| `postgresql.external.username` | Database username | `entelechy` |
| `ingress.enabled` | Enable ingress | `false` |
| `autoscaling.enabled` | Enable HPA | `false` |

### Environment Variables

All environment variables in `api.env` and `controlPlane.env` are automatically added to the respective pods. Sensitive values should go in `api.secrets` or `controlPlane.secrets`.

```yaml
api:
  env:
    ENTELECHY_API_LLM_PROVIDER: "openai"
    ENTELECHY_API_LLM_MODEL: "gpt-4"
  secrets:
    ENTELECHY_API_LLM_API_KEY: "your-api-key"
    ENTELECHY_API_LLM_BASE_URL: "https://api.openai.com/v1"

controlPlane:
  env:
    NODE_ENV: "production"
  secrets: {}
```

### External Database

To connect to an external PostgreSQL database:

```yaml
postgresql:
  enabled: false
  external:
    host: "my-postgres.example.com"
    port: 5432
    database: "entelechy"
    username: "entelechy"
    password: "your-password"
```

### Ingress

To expose the services via ingress:

```yaml
ingress:
  enabled: true
  className: "nginx"
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
  hosts:
    - host: entelechy.example.com
      paths:
        - path: /
          pathType: Prefix
          service: controlPlane
        - path: /api
          pathType: Prefix
          service: api
  tls:
    - secretName: entelechy-tls
      hosts:
        - entelechy.example.com
```

## Upgrading

```bash
helm upgrade entelechy ./helm/entelechy -n entelechy
```

## Uninstalling

```bash
helm uninstall entelechy -n entelechy
```

## Components

The chart deploys:

- **API**: The main Entelechy API server for memory operations
- **Control Plane**: Web UI for managing agents and viewing memories

## Development

### Lint the chart

```bash
helm lint ./helm/entelechy
```

### Template locally

```bash
helm template entelechy ./helm/entelechy --debug
```

### Dry run installation

```bash
helm install entelechy ./helm/entelechy --dry-run --debug
```
