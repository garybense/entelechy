import { describe, it, expect } from "vitest";
import { hasEntelechyPolicy, mergeEntelechyPolicy, serializePolicy } from "./policy-writer.js";
import { parseSandboxPolicy } from "./policy-reader.js";
import type { SandboxPolicy } from "./types.js";
import { ENTELECHY_HOST, OPENCLAW_BINARY } from "./types.js";

const BASE_POLICY: SandboxPolicy = {
  version: 1,
  filesystem_policy: {
    include_workdir: true,
    read_only: ["/usr", "/lib"],
    read_write: ["/sandbox", "/tmp"],
  },
  network_policies: {
    claude_code: {
      name: "claude_code",
      endpoints: [
        {
          host: "api.anthropic.com",
          port: 443,
          rules: [{ allow: { method: "*", path: "/**" } }],
        },
      ],
      binaries: [{ path: "/usr/local/bin/claude" }],
    },
  },
};

describe("hasEntelechyPolicy", () => {
  it("returns false when no entelechy policy exists", () => {
    expect(hasEntelechyPolicy(BASE_POLICY)).toBe(false);
  });

  it("returns false when network_policies is undefined", () => {
    expect(hasEntelechyPolicy({ version: 1 })).toBe(false);
  });

  it("returns true when entelechy policy is present", () => {
    const withEntelechy = mergeEntelechyPolicy(BASE_POLICY);
    expect(hasEntelechyPolicy(withEntelechy)).toBe(true);
  });
});

describe("mergeEntelechyPolicy", () => {
  it("adds the entelechy network policy block", () => {
    const result = mergeEntelechyPolicy(BASE_POLICY);
    expect(result.network_policies?.entelechy).toBeDefined();
    expect(result.network_policies?.entelechy?.endpoints[0].host).toBe(ENTELECHY_HOST);
  });

  it("preserves all existing network policies", () => {
    const result = mergeEntelechyPolicy(BASE_POLICY);
    expect(result.network_policies?.claude_code).toBeDefined();
    expect(result.network_policies?.claude_code?.name).toBe("claude_code");
  });

  it("sets the correct binary path", () => {
    const result = mergeEntelechyPolicy(BASE_POLICY);
    const binaries = result.network_policies?.entelechy?.binaries ?? [];
    expect(binaries.some((b) => b.path === OPENCLAW_BINARY)).toBe(true);
  });

  it("includes GET, POST, and PUT rules", () => {
    const result = mergeEntelechyPolicy(BASE_POLICY);
    const rules = result.network_policies?.entelechy?.endpoints[0].rules ?? [];
    const methods = rules.map((r) => r.allow.method);
    expect(methods).toContain("GET");
    expect(methods).toContain("POST");
    expect(methods).toContain("PUT");
  });

  it("is idempotent — merging twice yields the same result", () => {
    const once = mergeEntelechyPolicy(BASE_POLICY);
    const twice = mergeEntelechyPolicy(once);
    expect(JSON.stringify(twice.network_policies?.entelechy)).toBe(
      JSON.stringify(once.network_policies?.entelechy)
    );
  });

  it("does not mutate the original policy", () => {
    const original = JSON.parse(JSON.stringify(BASE_POLICY)) as SandboxPolicy;
    mergeEntelechyPolicy(BASE_POLICY);
    expect(BASE_POLICY.network_policies?.entelechy).toBeUndefined();
    expect(JSON.stringify(BASE_POLICY)).toBe(JSON.stringify(original));
  });
});

describe("serializePolicy", () => {
  it("produces valid YAML that round-trips through parseSandboxPolicy", () => {
    const merged = mergeEntelechyPolicy(BASE_POLICY);
    const yamlStr = serializePolicy(merged);
    // Wrap in Policy: header as parseSandboxPolicy expects
    const wrapped =
      "Policy:\n" +
      yamlStr
        .split("\n")
        .map((l) => `  ${l}`)
        .join("\n");
    const reparsed = parseSandboxPolicy(wrapped);
    expect(reparsed.version).toBe(merged.version);
    expect(reparsed.network_policies?.entelechy?.endpoints[0].host).toBe(ENTELECHY_HOST);
    expect(reparsed.network_policies?.claude_code).toBeDefined();
  });

  it("includes all network policies in output", () => {
    const merged = mergeEntelechyPolicy(BASE_POLICY);
    const yaml = serializePolicy(merged);
    expect(yaml).toContain("claude_code:");
    expect(yaml).toContain("entelechy:");
    expect(yaml).toContain(ENTELECHY_HOST);
  });
});
