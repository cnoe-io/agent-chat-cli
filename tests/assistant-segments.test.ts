import { describe, expect, it } from "vitest";
import { splitAssistantSegments } from "../src/platform/terminal/assistant-segments.js";
import { formatToolTreeLabel } from "../src/platform/terminal/tool-label.js";

describe("splitAssistantSegments", () => {
  it("pulls fenced diff into diff segment", () => {
    const md = "Intro\n\n```diff\n--- a\n+++ b\n@@ -1 +1 @@\n-old\n+new\n```\n\nDone";
    const segs = splitAssistantSegments(md);
    expect(segs.some((s) => s.kind === "diff" && s.text.includes("-old"))).toBe(true);
    expect(segs.some((s) => s.kind === "markdown" && s.text.includes("Intro"))).toBe(true);
  });
});

describe("formatToolTreeLabel", () => {
  it("formats file tools as Update(path)", () => {
    expect(formatToolTreeLabel("write_file", '{"path":".github/workflows/release.yml"}')).toBe(
      "Update(.github/workflows/release.yml)",
    );
  });
});
