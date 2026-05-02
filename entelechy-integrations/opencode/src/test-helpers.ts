import type { EntelechyConfig } from "./config.js";

export function makeConfig(overrides: Partial<EntelechyConfig> = {}): EntelechyConfig {
  return {
    autoRecall: true,
    recallBudget: "mid",
    recallMaxTokens: 1024,
    recallTypes: ["world", "experience"],
    recallContextTurns: 1,
    recallMaxQueryChars: 800,
    recallPromptPreamble: "",
    recallTags: [],
    recallTagsMatch: "any",
    autoRetain: true,
    retainMode: "full-session",
    retainEveryNTurns: 3,
    retainOverlapTurns: 2,
    retainContext: "opencode",
    retainTags: [],
    retainMetadata: {},
    entelechyApiUrl: null,
    entelechyApiToken: null,
    bankId: null,
    bankIdPrefix: "",
    dynamicBankId: false,
    dynamicBankGranularity: ["agent", "project"],
    bankMission: "",
    retainMission: null,
    agentName: "opencode",
    debug: false,
    ...overrides,
  };
}
