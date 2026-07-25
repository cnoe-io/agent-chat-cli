import { afterEach, describe, expect, it } from "vitest";
import { isShellHitlEnabled, shellApprovalTitle } from "../src/chat/shell-hitl.js";

describe("shell-hitl", () => {
  const env = process.env;

  afterEach(() => {
    process.env = { ...env };
  });

  it("enables HITL by default", () => {
    delete process.env.CAIPE_SHELL_AUTO_APPROVE;
    delete process.env.CAIPE_HITL_SHELL;
    expect(isShellHitlEnabled()).toBe(true);
  });

  it("disables HITL when CAIPE_SHELL_AUTO_APPROVE is set", () => {
    process.env.CAIPE_SHELL_AUTO_APPROVE = "1";
    expect(isShellHitlEnabled()).toBe(false);
  });

  it("disables HITL when CAIPE_HITL_SHELL=0", () => {
    process.env.CAIPE_HITL_SHELL = "0";
    expect(isShellHitlEnabled()).toBe(false);
  });

  it("titles escape vs pipe", () => {
    expect(shellApprovalTitle("escape")).toContain("shell");
    expect(shellApprovalTitle("pipe")).toContain("Pipe");
  });
});
