import { describe, expect, it } from "vitest";
import { bankRoute, bankApi, bankStatsApi, memoryApi, documentApi } from "./bank-url";

describe("bank-url helper functions", () => {
  describe("bankRoute", () => {
    it("formats standard bank routes without suffix", () => {
      expect(bankRoute("bank123")).toBe("/banks/bank123");
    });

    it("formats bank routes with a suffix", () => {
      expect(bankRoute("bank123", "/settings")).toBe("/banks/bank123/settings");
    });

    it("percent-encodes special characters in bankId", () => {
      // openclaw style composite id containing colons
      expect(bankRoute("agent-1::channel-2::user-3")).toBe(
        "/banks/agent-1%3A%3Achannel-2%3A%3Auser-3"
      );
      // slashes, spaces, and percent signs
      expect(bankRoute("foo/bar baz%1")).toBe("/banks/foo%2Fbar%20baz%251");
    });
  });

  describe("bankApi", () => {
    it("formats standard proxy API path without suffix", () => {
      expect(bankApi("my-bank")).toBe("/api/banks/my-bank");
    });

    it("formats proxy API path with suffix", () => {
      expect(bankApi("my-bank", "/memories")).toBe("/api/banks/my-bank/memories");
    });

    it("percent-encodes special characters in bankId", () => {
      expect(bankApi("user/123::bank")).toBe("/api/banks/user%2F123%3A%3Abank");
    });
  });

  describe("bankStatsApi", () => {
    it("formats bank stats proxy API path without suffix", () => {
      expect(bankStatsApi("bank-id")).toBe("/api/stats/bank-id");
    });

    it("formats bank stats proxy API path with suffix", () => {
      expect(bankStatsApi("bank-id", "?time=24h")).toBe("/api/stats/bank-id?time=24h");
    });

    it("percent-encodes special characters in bankId", () => {
      expect(bankStatsApi("complex:bank/id")).toBe("/api/stats/complex%3Abank%2Fid");
    });
  });

  describe("memoryApi", () => {
    it("formats memory endpoint with bank_id query string parameter when suffix has no query string", () => {
      expect(memoryApi("mem-1", "bank-1")).toBe("/api/memories/mem-1?bank_id=bank-1");
    });

    it("appends bank_id with '&' when suffix already includes a query string '?'", () => {
      expect(memoryApi("mem-1", "bank-1", "?include_vector=true")).toBe(
        "/api/memories/mem-1?include_vector=true&bank_id=bank-1"
      );
    });

    it("appends bank_id with '?' when suffix is a subpath without query params", () => {
      expect(memoryApi("mem-1", "bank-1", "/details")).toBe(
        "/api/memories/mem-1/details?bank_id=bank-1"
      );
    });

    it("percent-encodes both memoryId and bankId", () => {
      expect(memoryApi("mem/123:abc", "bank:456/def")).toBe(
        "/api/memories/mem%2F123%3Aabc?bank_id=bank%3A456%2Fdef"
      );
    });
  });

  describe("documentApi", () => {
    it("formats document endpoint with bank_id query string parameter", () => {
      expect(documentApi("doc-123", "bank-456")).toBe("/api/documents/doc-123?bank_id=bank-456");
    });

    it("percent-encodes both documentId and bankId", () => {
      expect(documentApi("doc/123::v1", "user@domain.com::bank")).toBe(
        "/api/documents/doc%2F123%3A%3Av1?bank_id=user%40domain.com%3A%3Abank"
      );
    });
  });
});
