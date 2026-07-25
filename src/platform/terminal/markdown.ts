/**
 * Markdown rendering entry points.
 *
 * Interactive UI: {@link AnsiMarkdown} (marked-terminal ANSI in Ink Text).
 * Headless stdout: {@link renderMarkdown}.
 */

export {
  getMarkdownLayoutWidth,
  getTerminalCapabilities,
  getTerminalWidth,
  isRichTerminalEnabled,
} from "./capabilities.js";
export { InkDiffBlock } from "./ink-diff.js";
export { AssistantBody } from "./AssistantBody.js";
export { AnsiMarkdown } from "./AnsiMarkdown.js";
export { plainTextFromMarkdown, renderMarkdownToAnsi } from "./ansi-markdown.js";

import { renderMarkdownToAnsi } from "./ansi-markdown.js";

/** @deprecated No global renderer cache; kept for resize hooks. */
export function refreshMarkdownTerminalWidth(): void {}

/** Headless / skills stdout (ANSI when TTY allows). */
export function renderMarkdown(text: string, width?: number): string {
  return renderMarkdownToAnsi(text, { width });
}
