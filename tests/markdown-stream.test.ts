import { describe, expect, it } from "vitest";
import {
  MarkdownStreamSession,
  partitionMarkdown,
  remendMarkdownTail,
} from "../src/chat/markdown-stream.js";
import { isUnifiedDiffText } from "../src/platform/diff.js";
import { plainTextFromMarkdown } from "../src/platform/markdown.js";

describe("partitionMarkdown", () => {
  it("splits on blank lines outside fences", () => {
    const { stableBlocks, tailBlock } = partitionMarkdown("Hello\n\nWorld");
    expect(stableBlocks).toEqual(["Hello"]);
    expect(tailBlock).toBe("World");
  });

  it("keeps fenced code in one block", () => {
    const src = "Intro\n\n```js\nconst x = 1\n```\n\nAfter";
    const { stableBlocks, tailBlock } = partitionMarkdown(src);
    expect(stableBlocks.some((b) => b.includes("```js"))).toBe(true);
    expect(tailBlock).toBe("After");
  });
});

describe("remendMarkdownTail", () => {
  it("closes open fence", () => {
    expect(remendMarkdownTail("```ts\nconst a = 1")).toContain("```");
  });
});

describe("isUnifiedDiffText", () => {
  it("detects unified diff headers", () => {
    const diff = "--- a/foo\n+++ b/foo\n@@ -1 +1 @@\n-old\n+new";
    expect(isUnifiedDiffText(diff)).toBe(true);
  });
});

describe("MarkdownStreamSession", () => {
  it("only extends stable cache when a new block completes", () => {
    const session = new MarkdownStreamSession();
    const a = session.sync("Block one");
    expect(a.tailDisplay.length).toBeGreaterThan(0);

    const b = session.sync("Block one\n\nBlock two");
    expect(b.tailDisplay).toMatch(/Block two/);
  });

  it("drains stable blocks for Static append", () => {
    const session = new MarkdownStreamSession();
    session.sync("Done block\n\nTail");
    const drained = session.drainNewStableBlocks();
    expect(drained.length).toBe(1);
    expect(session.drainNewStableBlocks()).toEqual([]);
  });
});

describe("plainTextFromMarkdown", () => {
  it("strips basic markers", () => {
    expect(plainTextFromMarkdown("**bold** and `code`")).toBe("bold and code");
  });
});
