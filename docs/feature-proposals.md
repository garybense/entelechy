# Entelechy Architecture & Feature Proposals

## Executive Summary

Entelechy is a Memory-Weighted Policy Modulation Controller (MWPMC). Unlike traditional RAG or static long-term memory systems, Entelechy treats memory not as a passive database, but as an active middleware that conditions generative AI models at runtime.

This document outlines four high-impact feature proposals designed to automate agent onboarding over Model Context Protocol (MCP), enhance developer observation and interactive debugging in the Control Plane, introduce background episodic consolidation, and implement dynamic runtime policy modulation.

---

## Feature 1: MCP Auto-Bootstrapping & Dynamic Tool Adaptive Binding (Zero-Touch Agent Onboarding Protocol)

### Abstract
Currently, when an AI model or client connects to Entelechy over MCP (via HTTP SSE or stdio), the agent receives basic static instructions and tool definitions. However, the model must manually choose when and how to query or initialize memory, leading to cold-start problems and inconsistent tool adoption. This proposal introduces an **Automated MCP Handshake & Auto-Bootstrap Protocol**, which automatically injects user identity, policy state vectors, and active directives directly into the MCP connection payload during the initial handshake, binding the agent's behavior from token 0.

### Problem Statement
- **Cold-Start Delays:** Agents connecting via MCP don't automatically know the bank state, user preferences, or active mental models unless they explicitly execute `recall` or `get_bank` tool calls.
- **Inconsistent Tool Usage:** LLMs often forget to execute background writebacks (`retain`) or fail to adhere to bank disposition parameters (skepticism, empathy, literalism).

### Technical Architecture & Flow
1. **MCP Connection Hijack / Initial Prompt Hook:** When an MCP client initializes (`initialize` / `notifications/initialized`), Entelechy's MCP server automatically executes a lightweight `/bootstrap` pipeline for the resolved `bank_id`.
2. **Context Injection Payload:** The server appends a dynamic `system_prompt_snippet` and initial `State Vector (Vector P)` directly into the server capabilities / prompt template response.
3. **Adaptive Tool Binding:** Based on the bank's active tools configuration and disposition traits, the server dynamically filters and customizes tool descriptions (e.g., instructing the agent precisely when `sync_retain` vs `retain` should be invoked).

### API & Schema Design
```typescript
interface MCPBootstrapHandshakeResponse {
  mcp_version: string;
  bank_id: string;
  state_vector: {
    disposition: { skepticism: number; literalism: number; empathy: number };
    active_directives: string[];
    top_mental_models: string[];
  };
  injected_system_instructions: string;
  bound_tools: string[];
}
```

---

## Feature 2: Interactive MCP Tool-Use Sandbox & Debugger in Control Plane

### Abstract
While Entelechy features a Next.js Control Plane UI, developers lack a dedicated, real-time playground to simulate, debug, and inspect MCP protocol exchanges, tool calls, and state vector modulations before deploying agents to production. This feature adds an **Interactive MCP Tool-Use Sandbox** inside `entelechy-control-plane`.

### Problem Statement
- Developers currently have to test MCP integrations using external tools or terminal CLI commands.
- It is difficult to observe how an LLM reacts to policy vector injections, disposition changes, and retention writebacks in real-time.

### Technical Architecture & Flow
1. **Control Plane Playground View (`/banks/[id]?view=mcp-sandbox`):** A cybernetic GUI component rendering live MCP tool requests, responses, and state changes.
2. **Mock Agent / MCP Client Emulator:** An embedded client runner that opens an SSE/Stdio stream to Entelechy's `/mcp/{bank_id}` endpoint.
3. **Visual State Inspection:** Side-by-side inspection of:
   - Injected Prompt Modulations (Vector P)
   - Tool execution traces & response latencies
   - Resulting Memory Graph updates (nodes & entity links added via `retain`)

### Component Breakdown
- `MCPSandboxView.tsx`: Main dashboard UI with SSE stream loggers.
- `ToolInvocationInspector.tsx`: Detailed JSON tree viewer for FastMCP payloads.
- `PolicyVectorGauge.tsx`: Visual radar chart displaying real-time bank disposition parameters.

---

## Feature 3: Automated Episodic Consolidation & Memory Graph Pruning Engine

### Abstract
Over extended agent interactions, the episodic memory graph accumulates raw `[EXPERIENCE]` facts and redundant observations. This feature introduces a background **Episodic Consolidation Engine** in `entelechy-api` that automatically clusters raw episodic memories, synthesizes higher-level mental models, and prunes stale or contradicted graph links.

### Problem Statement
- Raw memory buildup increases retrieval vector noise and token overhead during `recall` operations.
- Mental models currently require explicit API creation or manual refresh commands.

### Technical Architecture & Flow
1. **Async Worker / Cron Pipeline:** A background worker runs periodic consolidation cycles per memory bank.
2. **Semantic Clustering & Link Analysis:** Using embedding distances and graph community detection, related `[EXPERIENCE]` items are grouped.
3. **Abstractive Synthesis:** An LLM worker synthesizes cluster themes into structured **Mental Models** and **Directives**.
4. **Decay & Pruning:** Low-relevance, un-reinforced episodic links are assigned a temporal decay factor and archived.

### Key Metrics & Config
- `ENTELECHY_API_CONSOLIDATION_INTERVAL`: Cron schedule (e.g. daily/hourly).
- `ENTELECHY_API_MIN_CLUSTER_SIZE`: Minimum raw facts required to trigger mental model synthesis (default: 5).

---

## Feature 4: Adaptive MCP Policy Modulation Middleware (Contextual Tool Gating & Skill Binding)

### Abstract
Agents operating in complex environments require different tools depending on task context. This feature adds a **Contextual Policy Modulation Middleware** to Entelechy's FastMCP server that dynamically exposes, hides, or modifies MCP tool declarations based on real-time task intent and memory state.

### Problem Statement
- Presenting 30+ MCP tools simultaneously to an LLM inflates prompt size, increases latency, and increases the rate of tool-selection errors.
- Certain high-consequence tools (e.g., `delete_bank`, `clear_memories`) should only be bound when explicit confirmation context is detected.

### Technical Architecture & Flow
1. **Dynamic Tool Resolver:** On each MCP tool request or session prompt turn, Entelechy evaluates the current query context against the bank state.
2. **Tool Gating Rules:** FastMCP server dynamically filters `list_tools()` responses based on active intent (e.g. standard conversation mode exposes `recall`/`retain`; administrative mode exposes `create_mental_model`).
3. **Safety & Compliance Gating:** Prevents accidental invocation of destructive operations by enforcing multi-step policy checks.

---

## Summary Roadmap & Implementation Priority

1. **Phase 1 (Immediate Impact):** MCP Auto-Bootstrapping & Zero-Touch Onboarding (Feature 1).
2. **Phase 2 (Developer Experience):** Control Plane MCP Sandbox & Debugger (Feature 2).
3. **Phase 3 (Engine Optimizations):** Automated Episodic Consolidation Engine (Feature 3).
4. **Phase 4 (Enterprise & Safety):** Adaptive Tool Gating & Dynamic Skill Binding Middleware (Feature 4).
