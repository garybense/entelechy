---
title: "Guide: Set Up ContextForge Memory with Entelechy"
authors: [benfrank241]
date: 2026-04-16
tags: [how-to, contextforge, mcp, memory]
description: "Set up ContextForge memory with Entelechy so every client behind the gateway can use retain, recall, and reflect through one unified MCP endpoint."
image: /img/blog/guide-contextforge-memory-with-entelechy.png
hide_table_of_contents: true
---

![Guide: Set Up ContextForge Memory with Entelechy](/img/blog/guide-contextforge-memory-with-entelechy.png)

If you want **ContextForge memory with Entelechy**, the core idea is simple: register Entelechy as an MCP backend inside ContextForge, then let your AI tools connect to ContextForge instead of talking to Entelechy directly. That gives you one gateway, one authentication layer, and one place to expose long-term memory to every compatible client.

This is a strong pattern for teams because ContextForge already solves gateway problems like auth, RBAC, and central endpoint management. Entelechy adds the memory layer on top: retain for storing durable context, recall for searching it, and reflect for synthesizing what the system has learned over time.

This guide walks through the registration flow, explains when single-bank vs multi-bank mode matters, and shows how to verify that Entelechy tools are actually surfacing through ContextForge. Keep the [docs home](https://entelechy.vectorize.io/docs) and the [quickstart guide](https://entelechy.vectorize.io/docs/quickstart) nearby while you work.

<!-- truncate -->

> **Quick answer**
>
> 1. Run Entelechy and ContextForge so they can reach each other.
> 2. Register Entelechy as an MCP server in ContextForge.
> 3. Choose whether ContextForge should expose Entelechy in single-bank or multi-bank mode.
> 4. Connect your client to ContextForge's endpoint, not directly to Entelechy.
> 5. Verify that retain, recall, and reflect are visible and callable.

## Prerequisites

Before you start, make sure you have:

- A running Entelechy deployment, either local, Kubernetes, or Cloud
- A running ContextForge instance
- Network connectivity from ContextForge to Entelechy
- Admin access to the ContextForge registration flow

If you are still deciding how to run Entelechy itself, start with [Entelechy Cloud](https://entelechy.vectorize.io) or the [quickstart guide](https://entelechy.vectorize.io/docs/quickstart) before adding the gateway layer.

## Why pair ContextForge with Entelechy

ContextForge is useful when you want a single MCP entry point for several systems. Entelechy is useful when your agents need durable memory instead of a stateless prompt loop. Put them together and you get:

- one authenticated endpoint for many MCP backends
- memory exposed alongside your other servers
- centralized access control
- the ability to scope memory by team or bank design

This is cleaner than wiring Entelechy directly into every downstream client one by one.

## Option 1: Register Entelechy in the ContextForge UI

Inside ContextForge:

1. Sign in as an admin.
2. Open **Servers**.
3. Click **Add Server**.
4. Fill in:
   - **Name**: `entelechy`
   - **URL**: your Entelechy MCP endpoint, usually `http://<host>:8888/mcp`
   - **Transport**: Streamable HTTP
5. Save the server.

That is the fastest path when you are testing or doing one-off setup.

## Option 2: Register Entelechy through the admin API

If you prefer automation, register the server through the ContextForge API.

```bash
TOKEN=$(curl -s -X POST https://your-contextforge.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "your-password"}' \
  | jq -r '.access_token')

curl -X POST https://your-contextforge.com/admin/servers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "entelechy",
    "url": "http://entelechy-api:8888/mcp",
    "transport": "streamable_http",
    "description": "Entelechy memory"
  }'
```

This approach is useful when you want repeatable environment setup instead of manual admin clicks.

## Single-bank vs multi-bank mode

Entelechy's MCP endpoint supports two patterns.

### Multi-bank mode

Use the root MCP path:

```text
http://entelechy-api:8888/mcp
```

This exposes bank management tools and lets clients choose or create banks dynamically.

Use this when:

- many teams or workflows need different banks
- the gateway needs flexibility
- you want runtime bank selection

### Single-bank mode

Use a bank-pinned URL:

```text
http://entelechy-api:8888/mcp/my-team-bank/
```

This removes bank selection from the client side and pins all memory operations to one bank.

Use this when:

- one ContextForge team should map to one shared memory bank
- you want simpler client behavior
- you want tighter isolation by configuration

For deeper recall behavior, see [Entelechy's recall API](https://entelechy.vectorize.io/docs/api/recall). For storage semantics, see [Entelechy's retain API](https://entelechy.vectorize.io/docs/api/retain).

## Connect clients to ContextForge

Once Entelechy is registered, clients should connect to ContextForge's MCP endpoint instead of Entelechy directly.

For example, Claude Desktop might use:

```json
{
  "mcpServers": {
    "context-forge": {
      "url": "https://your-contextforge.com/mcp",
      "headers": {
        "Authorization": "Bearer <your-contextforge-token>"
      }
    }
  }
}
```

From the client's point of view, Entelechy is now just one capability behind the gateway.

## Verify the tools are present

After registration, list tools through ContextForge and confirm Entelechy appears.

```bash
curl -s -X POST https://your-contextforge.com/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}'
```

You should see Entelechy tools such as retain, recall, and reflect.

A practical test is:

1. store a fact with retain
2. recall it through the gateway
3. ask reflect for a synthesis over the saved memory

If all three work through ContextForge, the integration is doing what it should.

## Common mistakes

### Registering the wrong Entelechy URL

Make sure you point ContextForge at Entelechy's MCP path, not just the API root.

### Choosing multi-bank when you really want strict isolation

If a team should always operate in one bank, a bank-pinned URL is often simpler and safer.

### Testing Entelechy directly instead of through ContextForge

That proves Entelechy works, but not that the gateway registration is correct.

### Forgetting to verify permissions

If ContextForge auth is mis-scoped, the Entelechy server can be healthy while the client still cannot use the tools.

## FAQ

### Should every client connect to Entelechy directly?

Not if ContextForge is the pattern you want. The point of the gateway is to centralize the connection surface.

### Is Entelechy Cloud compatible with this pattern?

Yes. The key question is whether ContextForge can reach the Entelechy endpoint you register.

### When should I use a bank per team?

When memory should be shared inside a team but isolated from other teams.

### Is this better than adding Entelechy to each tool manually?

For teams with many tools, usually yes. For a single client, direct setup is often simpler.

## Next Steps

- Start with [Entelechy Cloud](https://entelechy.vectorize.io) if you want the easiest managed backend
- Read the [full Entelechy docs](https://entelechy.vectorize.io/docs)
- Follow the [quickstart guide](https://entelechy.vectorize.io/docs/quickstart)
- Review [Entelechy's recall API](https://entelechy.vectorize.io/docs/api/recall)
- Review [Entelechy's retain API](https://entelechy.vectorize.io/docs/api/retain)
- Compare cross-tool memory patterns in [Team Shared Memory for AI Coding Agents](https://entelechy.vectorize.io/blog/team-shared-memory-ai-coding-agents)
