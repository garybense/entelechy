import { describe, it, expect } from "vitest";
import { getEmbedCommand } from "./command.js";

describe("getEmbedCommand", () => {
  it("defaults to uvx entelechy-embed@latest", () => {
    expect(getEmbedCommand()).toEqual(["uvx", "entelechy-embed@latest"]);
  });

  it("honours an explicit version", () => {
    expect(getEmbedCommand({ embedVersion: "0.5.0" })).toEqual(["uvx", "entelechy-embed@0.5.0"]);
  });

  it("treats an empty version as latest", () => {
    expect(getEmbedCommand({ embedVersion: "" })).toEqual(["uvx", "entelechy-embed@latest"]);
  });

  it("uses uv run --directory when a local path is given", () => {
    expect(getEmbedCommand({ embedPackagePath: "/abs/path" })).toEqual([
      "uv",
      "run",
      "--directory",
      "/abs/path",
      "entelechy-embed",
    ]);
  });

  it("local path takes precedence over version", () => {
    expect(getEmbedCommand({ embedPackagePath: "/abs/path", embedVersion: "0.5.0" })).toEqual([
      "uv",
      "run",
      "--directory",
      "/abs/path",
      "entelechy-embed",
    ]);
  });
});
