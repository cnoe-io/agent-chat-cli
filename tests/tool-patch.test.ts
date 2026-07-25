import { describe, expect, it } from "vitest";
import {
  patchFromToolArgs,
  patchFromToolCall,
  patchFromToolResult,
} from "../src/chat/tool-patch.js";
import { isUnifiedDiffText } from "../src/platform/diff.js";

describe("patchFromToolArgs", () => {
  it("builds unified diff from old_string / new_string", () => {
    const args = JSON.stringify({
      path: "src/foo.ts",
      old_string: "const a = 1;\n",
      new_string: "const a = 2;\n",
    });
    const patch = patchFromToolArgs("str_replace_editor", args);
    expect(patch).not.toBeNull();
    expect(patch?.path).toBe("src/foo.ts");
    expect(isUnifiedDiffText(patch?.unifiedDiff ?? "")).toBe(true);
    expect(patch?.unifiedDiff).toContain("-const a = 1;");
    expect(patch?.unifiedDiff).toContain("+const a = 2;");
  });

  it("ignores non-file tools", () => {
    const args = JSON.stringify({ old_string: "a", new_string: "b" });
    expect(patchFromToolArgs("search_confluence", args)).toBeNull();
  });
});

describe("patchFromToolResult", () => {
  it("accepts raw unified diff in content", () => {
    const diff = `--- a.txt
+++ b.txt
@@ -1 +1 @@
-old
+new
`;
    const patch = patchFromToolResult("write_file", diff);
    expect(patch?.unifiedDiff).toContain("+new");
  });

  it("reads patch field from JSON envelope", () => {
    const diff = `--- x
+++ x
@@ -1 +1 @@
-a
+b
`;
    const content = JSON.stringify({ path: "x.ts", patch: diff });
    const patch = patchFromToolResult("apply_patch", content);
    expect(patch?.path).toBe("x.ts");
    expect(patch?.unifiedDiff).toBe(diff.trim());
  });

  it("unwraps nested result JSON", () => {
    const inner = JSON.stringify({
      file_path: "README.md",
      old_string: "hello",
      new_string: "hello world",
    });
    const content = JSON.stringify({ result: inner });
    const patch = patchFromToolResult("edit_file", content);
    expect(patch?.unifiedDiff).toContain("+hello world");
  });
});

describe("patchFromToolCall", () => {
  it("prefers tool result over args", () => {
    const args = JSON.stringify({ old_string: "x", new_string: "y", path: "a.ts" });
    const result = JSON.stringify({ old_string: "1", new_string: "2", path: "b.ts" });
    const patch = patchFromToolCall("write", args, result);
    expect(patch?.unifiedDiff).toContain("+2");
    expect(patch?.unifiedDiff).not.toContain("+y");
  });
});
