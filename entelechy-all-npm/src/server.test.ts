import { describe, it, expect } from "vitest";
import { EntelechyServer } from "./server.js";

describe("EntelechyServer construction", () => {
  it("defaults base URL to http://127.0.0.1:8888", () => {
    const server = new EntelechyServer();
    expect(server.getBaseUrl()).toBe("http://127.0.0.1:8888");
    expect(server.getProfile()).toBe("default");
  });

  it("honours custom profile, port, and host", () => {
    const server = new EntelechyServer({ profile: "app", port: 9077, host: "0.0.0.0" });
    expect(server.getProfile()).toBe("app");
    expect(server.getBaseUrl()).toBe("http://0.0.0.0:9077");
  });

  it("accepts open env pass-through without complaining about unknown keys", () => {
    const server = new EntelechyServer({
      env: {
        ENTELECHY_API_LLM_PROVIDER: "openai",
        ENTELECHY_API_LLM_MODEL: "gpt-4o-mini",
        // A field that does not exist today — should still be accepted
        ENTELECHY_FUTURE_FLAG: "enabled",
      },
    });
    expect(server).toBeInstanceOf(EntelechyServer);
  });

  it("exposes checkHealth that returns false when no daemon is running", async () => {
    // Random high port that nothing is listening on.
    const server = new EntelechyServer({ port: 1, readyTimeoutMs: 100 });
    const healthy = await server.checkHealth();
    expect(healthy).toBe(false);
  });
});
