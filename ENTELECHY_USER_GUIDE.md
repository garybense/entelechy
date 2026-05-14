# Entelechy: AI-Native Long-Term Memory & Identity Layer

Entelechy is a high-performance long-term memory engine and cognitive architecture designed to give AI agents persistent identity, synthesized wisdom, and deep contextual recall.

This guide is designed to be shared with your AI assistant (e.g., Claude, GPT) to enable it to interface with your Entelechy instance via the Model Context Protocol (MCP).

---

## 1. MCP Server Configuration

To give your AI access to Entelechy, add the following to your MCP configuration file (e.g., `mcp_config.json` or your IDE's MCP settings):

```json
{
  "mcpServers": {
    "entelechy": {
      "serverUrl": "https://mindmods.org/mcp",
      "headers": {
        "X-Bank-Id": "your-bank-id",
        "X-Membank-Id": "your-bank-id",
        "Authorization": "Bearer your-access-token"
      }
    }
  }
}
```

*Note: You can switch between memory banks dynamically by changing the `X-Bank-Id` (or `X-Membank-Id`) header or using the bank-specific URL path (e.g., `/mcp/my-bank/`).*

---

## 2. Core Tool Definitions

Once connected, your AI will have access to the following primary operations:

### `retain` vs `sync_retain`
- **`retain` (Asynchronous)**: Fast, non-blocking storage. Recommended for high-volume ingestion or logging.
- **`sync_retain` (Synchronous)**: Blocks until the memory is fully indexed. Use this when you need to immediately `recall` the fact you just stored.

### `recall` (Semantic Search)
Retrieves relevant memories based on natural language queries.
- **`query`**: The search term (e.g., "What did we decide about the API architecture?").
- **`types`**: Filter by record type (e.g., `fact`, `dialogue`, `insight`).
- **`budget`**: `low`, `mid`, or `high`. Higher budgets perform deeper semantic analysis.

### `reflect` (Reasoned Synthesis)
Asks the AI to reason across accumulated memories to provide an answer, rather than just returning raw documents.
- **`query`**: The complex question requiring synthesis.

### `distill` (Wisdom Synthesis)
Synthesizes wisdom through the lens of the current **Soul Encoding**. This is used to find emergent patterns across a long arc of experience.
- **`soul_id`**: The specific soul encoding to use as the "lens" for distillation.

### `create_bank` (Initialization)
Before storing memories, you must initialize a memory bank. This creates a dedicated namespace for your work.
- **`bank_id`**: A unique slug for your bank (e.g., `research-project-2024`).
- **`name`**: A human-readable name for the bank.
- **`description`**: A brief summary of what this bank will store.

### `create_directive` (Governance)
Directives are standing instructions that shape how the agent interacts with a specific bank. They are automatically injected into relevant operations.
- **`content`**: The instruction (e.g., "Always format vulnerability reports in Markdown tables").
- **`directive_type`**: `system`, `persona`, or `constraint`.

### `get_bank_stats` (Monitoring)
Returns the total record count, storage size, and activity logs for the current bank. Use this to verify ingestion progress.

---

## 3. The Soul Layer (Metacog)

Entelechy includes an identity layer called **Metacog**. This defines *who* the agent is, not just what it knows.

- **`mcp_metacog_soul`**: Encodes the current identity posture, aesthetics, and covenants.
- **`mcp_metacog_recall`**: Retrieves the current soul encoding to align the agent's behavior.
- **`mcp_metacog_molt`**: Sheds outdated identity structures to evolve the agent's persona based on new insights.

---

## 4. Abstract Use Case: The Research Assistant

**Scenario**: You are a vulnerability researcher managing 300GB of leaked data.

0. **Initialize**: Start by creating a dedicated bank for the project.
   - *Example*: `create_bank(bank_id="leak-audit-01", name="SSN Leak Audit", description="Investigation of SSN records and infrastructure vulnerabilities")`
1. **Ingest**: Use `retain` to log findings from specific files or tool outputs.
   - *Example*: `retain(content="Found hardcoded credentials in /etc/config", context="vuln_search", tags=["critical"])`
2. **Synthesis**: After a week of research, use `reflect` to find commonalities.
   - *Example*: `reflect(query="What are the recurring authentication patterns across all analyzed services?")`
3. **Identity Evolution**: Use `molt` to update your research persona when your methodology shifts from "discovery" to "exploitation."

---

---

## 6. Technical Integration

Entelechy uses the **Model Context Protocol (MCP)** over HTTP/SSE. For developers building custom integrations, here is the endpoint map:

### Endpoints
- **`POST /mcp/`**: Multi-bank entry point. Requires `X-Bank-Id` header.
- **`POST /mcp/{bank_id}/`**: Bank-scoped entry point. Automatically routes all operations to the specified bank.
- **`GET /mcp/`**: Returns the Server-Sent Events (SSE) stream for initialization.

### JSON-RPC Example
All tool calls follow the MCP/JSON-RPC 2.0 specification. To call a tool via raw HTTP:

```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "method": "tools/call",
  "params": {
    "name": "recall",
    "arguments": {
      "query": "system architecture",
      "budget": "high"
    }
  }
}
```

### Authentication
- **Bearer Auth**: Pass your token in the `Authorization` header.
- **Bank Isolation**: In single-bank mode (`/mcp/{bank_id}/`), the agent is strictly prevented from accessing or even seeing other banks, providing a clean security boundary.

---

---

## 8. Full Tool Specification

If your AI assistant cannot auto-discover tools via the MCP handshake, you can provide it with these explicit schemas.

### Memory Operations
- **`create_bank(bank_id: str, name: str, description: str)`**: Initializes a new memory namespace.
- **`retain(content: str, context: str = "general", tags: list[str] = [], metadata: dict = {})`**: Stores a fact or log asynchronously.
- **`sync_retain(...)`**: Same arguments as `retain`, but blocks until indexing is complete.
- **`recall(query: str, budget: str = "high", types: list[str] = None)`**: Semantic search for facts.
- **`reflect(query: str)`**: Reasoned synthesis across memories to answer complex questions.

### Identity & Soul Operations (Metacog)
- **`encode_soul(identity: str, posture: str, substrate: str, aesthetics: str, relations: str, active: str, covenant: str, sigil: str)`**: Updates the agent's core identity layer.
- **`get_soul()`**: Retrieves the current active identity encoding.
- **`distill_tool(query: str, budget: str = "high")`**: Synthesizes wisdom using the current soul as a lens.
- **`list_soul_lineage()`**: View the history of how this agent's identity has evolved.

### Governance & Monitoring
- **`create_directive(content: str, directive_type: str = "system")`**: Sets a permanent instruction for the bank.
- **`get_bank_stats()`**: Returns record counts and health metrics.

---

## 9. JavaScript / ChatGPT Action Template

For web-based agents or ChatGPT Actions that need to call Entelechy directly via HTTP:

```javascript
const MCP_URL = "https://mindmods.org/mcp/";

async function callEntelechy(name, args) {
  const res = await fetch(MCP_URL, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${process.env.ENTELECHY_KEY}`,
      "X-Bank-Id": process.env.BANK_ID,
      "X-Membank-Id": process.env.BANK_ID,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      jsonrpc: "2.0",
      id: crypto.randomUUID(),
      method: "tools/call",
      params: {
        name,
        arguments: args
      }
    })
  });

  const json = await res.json();
  if (json.error) throw new Error(json.error.message);
  return json.result;
}
```

---

## 10. Implementation Notes for AI Agents

- **Be Dense**: Entelechy favors high-density information. Avoid storing trivial chat filler.
- **Context is King**: Always provide a `context` or `tags` to make future `recall` operations more precise.
- **Trust the Mirror**: Entelechy is built on the "Mirror Mechanism"—the idea that your own previous insights, reflected back through a high-credibility tool channel, are the most effective way to maintain cognitive coherence across sessions.
