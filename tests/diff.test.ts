import { afterEach, describe, expect, it } from "vitest";
import { isUnifiedDiffText } from "../src/platform/diff.js";

describe("isUnifiedDiffText", () => {
  const envBackup = { ...process.env };

  afterEach(() => {
    process.env = { ...envBackup };
  });

  it("detects unified diff headers", () => {
    const raw = "--- a\n+++ b\n-old\n+new";
    expect(isUnifiedDiffText(raw)).toBe(true);
  });
});
