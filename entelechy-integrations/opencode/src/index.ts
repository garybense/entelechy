/**
 * Entelechy OpenCode Plugin — persistent long-term memory for OpenCode agents.
 *
 * Provides:
 *   - Custom tools: entelechy_retain, entelechy_recall, entelechy_reflect
 *   - Auto-retain on session.idle
 *   - Memory injection on session.created via system transform
 *   - Memory preservation during context compaction
 *
 * @example
 * ```json
 * // opencode.json
 * { "plugin": ["@vectorize-io/opencode-entelechy"] }
 *
 * // With options:
 * { "plugin": [["@vectorize-io/opencode-entelechy", { "bankId": "my-bank" }]] }
 * ```
 */

import type { Plugin } from "@opencode-ai/plugin";
import { EntelechyClient } from "@vectorize-io/entelechy-client";
import { loadConfig } from "./config.js";
import { deriveBankId } from "./bank.js";
import { createTools } from "./tools.js";
import { createHooks, type PluginState } from "./hooks.js";
import { debugLog } from "./config.js";

// Module-level state persists across sessions (plugin is instantiated per session,
// but the module is loaded once per OpenCode server process).
const state: PluginState = {
  turnCount: 0,
  missionsSet: new Set(),
  recalledSessions: new Set(),
  lastRetainedTurn: new Map(),
};

const EntelechyPlugin: Plugin = async (input, options) => {
  const config = loadConfig(options);

  const apiUrl = config.entelechyApiUrl;
  if (!apiUrl) {
    console.error(
      "[Entelechy] No API URL configured. Set ENTELECHY_API_URL environment variable " +
        "or add entelechyApiUrl to ~/.entelechy/opencode.json"
    );
    // Return empty hooks — graceful degradation
    return {};
  }

  const client = new EntelechyClient({
    baseUrl: apiUrl,
    apiKey: config.entelechyApiToken || undefined,
  });

  const bankId = deriveBankId(config, input.directory);
  debugLog(config, `Initialized with bank: ${bankId}, API: ${apiUrl}`);

  const tools = createTools(client, bankId, config, state.missionsSet);
  const hooks = createHooks(
    client,
    bankId,
    config,
    state,
    input.client as unknown as Parameters<typeof createHooks>[4]
  );

  return {
    tool: tools,
    ...hooks,
  };
};

// Named export for direct import
export { EntelechyPlugin };

// Default export is the Plugin function itself — OpenCode's loader calls the
// default export directly.
export default EntelechyPlugin;

// Re-export types for consumers
export type { EntelechyConfig } from "./config.js";
export type { PluginState } from "./hooks.js";
export { loadConfig } from "./config.js";
export { deriveBankId } from "./bank.js";
