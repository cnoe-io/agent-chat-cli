import React from "react";
import { render } from "ink";
import { describe, expect, it } from "vitest";
import { renderMarkdownToAnsi } from "../src/platform/terminal/ansi-markdown.js";
import { AnsiMarkdown } from "../src/platform/terminal/AnsiMarkdown.js";

const JIRA_TABLE = `Here are your issues:

| Key | Summary | Status | Updated |
| --- | --- | --- | --- |
| **EC2-1** | creation failed | Open | Jul 14 |
| **ARGO-2** | deploy failed | In Progress | May 22 |
`;

const GFM_LIST = "**Available agents**\n\n- **agent-sre** _(active)_ — SRE Agent";

describe("renderMarkdownToAnsi", () => {
  it("renders GFM tables as cli-table box (not raw pipe rows)", () => {
    const ansi = renderMarkdownToAnsi(
      `| Title | URL |
| --- | --- |
| CAIPE | https://wiki.example.com/display/COGNITIVE/CAIPE/overview/long/path |`,
      { width: 90, forceRich: true },
    );
    expect(ansi).toContain("┌");
    expect(ansi).not.toContain("mlink");
    expect(ansi).not.toMatch(/\x1b\]8;;[^\x1b]*link/i);
  });

  it("renders lists and headings without throwing in Ink", () => {
    expect(() => {
      render(React.createElement(AnsiMarkdown, {
        width: 80,
        children: GFM_LIST,
      })).unmount();
    }).not.toThrow();
  });

  it("strips to plain text when NO_COLOR", () => {
    const prev = process.env.NO_COLOR;
    process.env.NO_COLOR = "1";
    try {
      const out = renderMarkdownToAnsi("**bold**", { width: 80 });
      expect(out).toBe("bold");
    } finally {
      if (prev === undefined) delete process.env.NO_COLOR;
      else process.env.NO_COLOR = prev;
    }
  });

  it("does not truncate URLs inside markdown link hrefs in tables", () => {
    const long =
      "https://wiki.example.com/wiki/spaces/OPS/pages/123456789012345678901234567890/Title";
    const md = `| # | Title | Link |
| --- | --- | --- |
| 1 | Tome | [link](${long}) |`;
    const ansi = renderMarkdownToAnsi(md, { width: 72, forceRich: true });
    expect(ansi).toContain(long);
    expect(ansi).not.toContain(`${long.slice(0, 40)}…`);
  });

  it("renders GFM bullet lists with inline bold (marked v15)", () => {
    const md = `**Active Jira tasks:**\n\n* **OPENSD-2454** - Edge (Waiting)\n* **CFP-1** - foo`;
    const ansi = renderMarkdownToAnsi(md, { width: 100, forceRich: true });
    expect(ansi).toContain("• OPENSD-2454");
    expect(ansi).not.toContain("**OPENSD");
    expect(ansi).not.toMatch(/^\s+\*/m);
  });
});
