# @vectorize-io/entelechy-all

Node.js equivalent of the Python [`entelechy-all`](https://pypi.org/project/entelechy-all/) package — programmatic lifecycle manager for a local Entelechy daemon. Use this when you want to embed Entelechy in a Node application without hand-rolling subprocess management.

This package deliberately does **not** ship an HTTP client. Once the daemon is running, talk to it with [`@vectorize-io/entelechy-client`](https://www.npmjs.com/package/@vectorize-io/entelechy-client) against `server.getBaseUrl()`. The two packages compose — one owns the daemon process, the other owns the HTTP API surface.

## Requirements

- **Node.js >= 22** — uses global `fetch` and `AbortSignal.timeout`.
- **`uv` / `uvx`** on `PATH` — used to download and run the underlying `entelechy-embed` daemon on first use. Install via <https://docs.astral.sh/uv/>.

## Install

```bash
npm install @vectorize-io/entelechy-all @vectorize-io/entelechy-client
```

## Example

```ts
import { EntelechyServer, consoleLogger } from "@vectorize-io/entelechy-all";
import { EntelechyClient } from "@vectorize-io/entelechy-client";

const server = new EntelechyServer({
  profile: "my-app",
  port: 9077,
  env: {
    ENTELECHY_API_LLM_PROVIDER: "anthropic",
    ENTELECHY_API_LLM_API_KEY: process.env.ANTHROPIC_API_KEY,
    ENTELECHY_API_LLM_MODEL: "claude-sonnet-4-20250514",
    ENTELECHY_EMBED_DAEMON_IDLE_TIMEOUT: "0",
  },
  logger: consoleLogger,
});

await server.start();

const client = new EntelechyClient({ baseUrl: server.getBaseUrl() });

await client.retain("user-123", "User prefers dark mode and concise answers.", {
  documentId: "pref-2026-04-01",
});

const recall = await client.recall("user-123", "what are the user preferences?");
console.log(recall.results);

await server.stop();
```

For a remote Entelechy API, skip `EntelechyServer` entirely and just point `EntelechyClient` at the remote URL.

## Open config — forward-compatible with new daemon flags

`EntelechyServerOptions` is designed so every new environment variable or CLI flag in the underlying Entelechy daemon can be used without waiting for a wrapper release:

- **`env`** accepts an arbitrary `Record<string, string>`. Every entry is exported into the daemon process and written into the profile config via `--env KEY=VALUE`.
- **`extraProfileCreateArgs`** / **`extraDaemonStartArgs`** append raw args to the respective commands.

## Development against a local checkout

If you're hacking on the Python `entelechy-embed` package in the same monorepo, point the server at the local path — it'll use `uv run --directory <path>` instead of `uvx`:

```ts
new EntelechyServer({
  embedPackagePath: "/path/to/entelechy-embed",
  // ...
});
```

## API surface

- `EntelechyServer` — daemon lifecycle (`start`, `stop`, `checkHealth`, `getBaseUrl`, `getProfile`).
- `Logger` interface plus `silentLogger` (default) and `consoleLogger` helpers.
- `getEmbedCommand(opts)` — low-level helper that returns the `[cmd, ...args]` tuple used to invoke the underlying Python CLI.

For memory operations (retain, recall, reflect, bank management, stats) use [`@vectorize-io/entelechy-client`](https://www.npmjs.com/package/@vectorize-io/entelechy-client).

## License

MIT
