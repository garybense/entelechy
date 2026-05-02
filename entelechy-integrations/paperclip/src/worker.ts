/**
 * paperclip-plugin-entelechy — worker entrypoint.
 *
 * Gives Paperclip agents persistent long-term memory via Entelechy.
 *
 * Lifecycle:
 *   agent.run.started  → recall relevant memories, store in plugin state for the run
 *   agent.run.finished → retain agent output to Entelechy (if autoRetain is enabled)
 *
 * Agent tools (callable mid-run):
 *   entelechy_recall(query)   → search memory, returns relevant context
 *   entelechy_retain(content) → store content in memory immediately
 */

import { definePlugin, runWorker } from "@paperclipai/plugin-sdk";
import type { ToolRunContext } from "@paperclipai/plugin-sdk";
import { EntelechyClient, formatMemories } from "./client.js";
import { deriveBankId } from "./bank.js";

interface PluginConfig {
  entelechyApiUrl: string;
  entelechyApiKeyRef?: string;
  bankGranularity?: Array<"company" | "agent">;
  recallBudget?: "low" | "mid" | "high";
  autoRetain?: boolean;
}

interface RunStartedPayload {
  agentId: string;
  runId: string;
  issueTitle?: string;
  issueDescription?: string;
}

interface RunFinishedPayload {
  agentId: string;
  runId: string;
  output?: string;
  result?: string;
}

async function getConfig(ctx: {
  config: { get(): Promise<Record<string, unknown>> };
}): Promise<PluginConfig> {
  return (await ctx.config.get()) as unknown as PluginConfig;
}

async function resolveApiKey(
  ctx: { secrets: { resolve(ref: string): Promise<string | null> } },
  config: PluginConfig
): Promise<string | undefined> {
  if (!config.entelechyApiKeyRef) return undefined;
  const resolved = await ctx.secrets.resolve(config.entelechyApiKeyRef);
  return resolved ?? undefined;
}

const plugin = definePlugin({
  async setup(ctx) {
    ctx.logger.info("Entelechy memory plugin starting");

    // ---------------------------------------------------------------------------
    // agent.run.started — recall memories and cache them for this run
    // ---------------------------------------------------------------------------
    ctx.events.on("agent.run.started", async (event) => {
      const payload = event.payload as RunStartedPayload;
      const config = await getConfig(ctx);
      const { agentId, runId, issueTitle, issueDescription } = payload;
      const companyId = event.companyId;

      const query = [issueTitle, issueDescription].filter(Boolean).join("\n");
      if (!query.trim()) return;

      try {
        const apiKey = await resolveApiKey(ctx, config);
        const client = new EntelechyClient(config.entelechyApiUrl, apiKey);
        const bankId = deriveBankId({ companyId, agentId }, config);

        const response = await client.recall(bankId, query, config.recallBudget ?? "mid");

        const memories = formatMemories(response.results);
        if (memories) {
          await ctx.state.set(
            { scopeKind: "run", scopeId: runId, stateKey: "recalled-memories" },
            memories
          );
          ctx.logger.info("Recalled memories for run", {
            runId,
            bankId,
            count: response.results.length,
          });
        }
      } catch (err) {
        // Non-fatal: agent runs without memory context.
        ctx.logger.warn("Failed to recall memories on run start", {
          runId,
          error: String(err),
        });
      }
    });

    // ---------------------------------------------------------------------------
    // agent.run.finished — retain run output to Entelechy
    // ---------------------------------------------------------------------------
    ctx.events.on("agent.run.finished", async (event) => {
      const payload = event.payload as RunFinishedPayload;
      const config = await getConfig(ctx);

      if (config.autoRetain === false) return;

      const { agentId, runId, output, result } = payload;
      const companyId = event.companyId;
      const content = output ?? result;

      if (!content?.trim()) return;

      try {
        const apiKey = await resolveApiKey(ctx, config);
        const client = new EntelechyClient(config.entelechyApiUrl, apiKey);
        const bankId = deriveBankId({ companyId, agentId }, config);

        await client.retain(bankId, content, runId, { agentId, companyId, runId });
        ctx.logger.info("Retained run output to memory", { runId, bankId });
      } catch (err) {
        ctx.logger.warn("Failed to retain run output", {
          runId,
          error: String(err),
        });
      }
    });

    // ---------------------------------------------------------------------------
    // Tool: entelechy_recall
    // ---------------------------------------------------------------------------
    ctx.tools.register(
      "entelechy_recall",
      {
        displayName: "Recall from Memory",
        description: "Search Entelechy long-term memory for context relevant to a query.",
        parametersSchema: {
          type: "object",
          required: ["query"],
          properties: {
            query: { type: "string", description: "What to search for" },
          },
        },
      },
      async (params: unknown, runCtx: ToolRunContext) => {
        const { query } = params as { query: string };
        const config = await getConfig(ctx);
        const bankId = deriveBankId(
          { companyId: runCtx.companyId, agentId: runCtx.agentId },
          config
        );

        // Return cached memories from run start if available
        const cached = await ctx.state.get({
          scopeKind: "run",
          scopeId: runCtx.runId,
          stateKey: "recalled-memories",
        });
        if (cached && typeof cached === "string") {
          return { content: cached };
        }

        // Live recall fallback
        try {
          const apiKey = await resolveApiKey(ctx, config);
          const client = new EntelechyClient(config.entelechyApiUrl, apiKey);
          const response = await client.recall(bankId, query, config.recallBudget ?? "mid");
          const memories = formatMemories(response.results);
          return { content: memories || "No relevant memories found." };
        } catch (err) {
          return { content: `Memory recall failed: ${String(err)}` };
        }
      }
    );

    // ---------------------------------------------------------------------------
    // Tool: entelechy_retain
    // ---------------------------------------------------------------------------
    ctx.tools.register(
      "entelechy_retain",
      {
        displayName: "Save to Memory",
        description:
          "Store important facts, decisions, or outcomes in Entelechy long-term memory for future runs.",
        parametersSchema: {
          type: "object",
          required: ["content"],
          properties: {
            content: {
              type: "string",
              description: "The content to store in memory",
            },
          },
        },
      },
      async (params: unknown, runCtx: ToolRunContext) => {
        const { content } = params as { content: string };
        const config = await getConfig(ctx);
        const bankId = deriveBankId(
          { companyId: runCtx.companyId, agentId: runCtx.agentId },
          config
        );

        try {
          const apiKey = await resolveApiKey(ctx, config);
          const client = new EntelechyClient(config.entelechyApiUrl, apiKey);
          await client.retain(bankId, content, undefined, {
            agentId: runCtx.agentId,
            companyId: runCtx.companyId,
            runId: runCtx.runId,
          });
          return { content: "Memory saved." };
        } catch (err) {
          return { content: `Failed to save memory: ${String(err)}` };
        }
      }
    );

    ctx.logger.info("Entelechy memory plugin ready");
  },

  async onHealth() {
    return { status: "ok" };
  },

  async onValidateConfig(config) {
    const c = config as Partial<PluginConfig>;
    if (!c.entelechyApiUrl?.trim()) {
      return { ok: false, errors: ["entelechyApiUrl is required"] };
    }

    try {
      const client = new EntelechyClient(c.entelechyApiUrl);
      const healthy = await client.health();
      if (!healthy) {
        return {
          ok: false,
          errors: [`Cannot reach Entelechy at ${c.entelechyApiUrl}`],
        };
      }
    } catch (err) {
      return { ok: false, errors: [`Connection failed: ${String(err)}`] };
    }

    return { ok: true };
  },
});

export default plugin;
runWorker(plugin, import.meta.url);
