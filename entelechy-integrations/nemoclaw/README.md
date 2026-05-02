# entelechy-nemoclaw

One-command setup for [Entelechy](https://entelechy.vectorize.io) persistent memory on [NemoClaw](https://nemoclaw.ai) sandboxes.

NemoClaw runs [OpenClaw](https://openclaw.ai) inside an OpenShell sandbox with strict network egress policies. This package automates the full setup: installing the `entelechy-openclaw` plugin, configuring external API mode, merging the Entelechy egress rule into your sandbox policy, and restarting the gateway.

## Quick Start

```bash
npx @vectorize-io/entelechy-nemoclaw setup \
  --sandbox my-assistant \
  --api-url https://api.entelechy.vectorize.io \
  --api-token <your-api-key> \
  --bank-prefix my-sandbox
```

Get an API key at [Entelechy Cloud](https://ui.entelechy.vectorize.io/signup).

## Documentation

Full setup guide, pitfalls, and troubleshooting:

**[NemoClaw Integration Documentation](https://vectorize.io/entelechy/sdks/integrations/nemoclaw)**

Or see [NEMOCLAW.md](./NEMOCLAW.md) in this directory for a step-by-step walkthrough.

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

## What It Does

1. **Preflight** — verifies `openshell` and `openclaw` are installed
2. **Install plugin** — runs `openclaw plugins install @vectorize-io/entelechy-openclaw`
3. **Configure plugin** — writes external API mode config to `~/.openclaw/openclaw.json`
4. **Apply policy** — reads current sandbox policy, merges Entelechy egress rule, re-applies via `openshell policy set`
5. **Restart gateway** — runs `openclaw gateway restart`

## Links

- [Entelechy Documentation](https://vectorize.io/entelechy)
- [NemoClaw](https://nemoclaw.ai)
- [OpenClaw](https://openclaw.ai)
- [GitHub Repository](https://github.com/vectorize-io/entelechy)

## License

MIT
