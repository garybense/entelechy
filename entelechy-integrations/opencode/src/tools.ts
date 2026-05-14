/**
 * Custom tool definitions for the Entelechy OpenCode plugin.
 *
 * Registers entelechy_retain, entelechy_recall, and entelechy_reflect
 * as tools the agent can call explicitly.
 */

import { tool } from "@opencode-ai/plugin/tool";
import type { ToolDefinition } from "@opencode-ai/plugin/tool";
import type { EntelechyClient } from "@garybense/entelechy-client";
import type { EntelechyConfig } from "./config.js";
import { formatMemories, formatCurrentTime } from "./content.js";
import { ensureBankMission } from "./bank.js";

export interface EntelechyTools {
  entelechy_retain: ToolDefinition;
  entelechy_recall: ToolDefinition;
  entelechy_reflect: ToolDefinition;
}

export function createTools(
  client: EntelechyClient,
  bankId: string,
  config: EntelechyConfig,
  missionsSet?: Set<string>
): EntelechyTools {
  const entelechy_retain = tool({
    description:
      "Store information in long-term memory. Use this to remember important facts, " +
      "user preferences, project context, decisions, and anything worth recalling in future sessions. " +
      "Be specific — include who, what, when, and why.",
    args: {
      content: tool.schema
        .string()
        .describe("The information to remember. Be specific and self-contained."),
      context: tool.schema
        .string()
        .optional()
        .describe("Optional context about where this information came from."),
    },
    async execute(args) {
      if (missionsSet) {
        await ensureBankMission(client, bankId, config, missionsSet);
      }
      await client.retain(bankId, args.content, {
        context: args.context || config.retainContext,
        tags: config.retainTags.length ? config.retainTags : undefined,
        metadata: Object.keys(config.retainMetadata).length ? config.retainMetadata : undefined,
      });
      return "Memory stored successfully.";
    },
  });

  const entelechy_recall = tool({
    description:
      "Search long-term memory for relevant information. Use this proactively before " +
      "answering questions about past conversations, user preferences, project history, " +
      "or any topic where prior context would help. When in doubt, recall first.",
    args: {
      query: tool.schema
        .string()
        .describe("Natural language search query. Be specific about what you need to know."),
    },
    async execute(args) {
      const response = await client.recall(bankId, args.query, {
        budget: config.recallBudget as "low" | "mid" | "high",
        maxTokens: config.recallMaxTokens,
        types: config.recallTypes,
        tags: config.recallTags.length ? config.recallTags : undefined,
        tagsMatch: config.recallTags.length ? config.recallTagsMatch : undefined,
      });

      const results = response.results || [];
      if (!results.length) return "No relevant memories found.";

      const formatted = formatMemories(results);
      return `Found ${results.length} relevant memories (as of ${formatCurrentTime()} UTC):\n\n${formatted}`;
    },
  });

  const entelechy_reflect = tool({
    description:
      "Generate a thoughtful answer using long-term memory. Unlike recall (which returns " +
      "raw memories), reflect synthesizes memories into a coherent answer. Use for questions " +
      'like "What do you know about this user?" or "Summarize our project decisions."',
    args: {
      query: tool.schema.string().describe("The question to answer using long-term memory."),
      context: tool.schema
        .string()
        .optional()
        .describe("Optional additional context to guide the reflection."),
    },
    async execute(args) {
      if (missionsSet) {
        await ensureBankMission(client, bankId, config, missionsSet);
      }
      const response = await client.reflect(bankId, args.query, {
        context: args.context,
        budget: config.recallBudget as "low" | "mid" | "high",
      });

      return response.text || "No relevant information found to reflect on.";
    },
  });

  return { entelechy_retain, entelechy_recall, entelechy_reflect };
}
