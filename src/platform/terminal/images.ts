/**
 * Inline terminal images from markdown image syntax (iTerm2 / Kitty).
 */

import type { TerminalCapabilities } from "./capabilities.js";

const IMAGE_MD = /!\[([^\]]*)\]\(([^)\s]+)(?:\s+"([^"]*)")?\)/g;

function stripControlChars(value: string): string {
  let out = "";
  for (const ch of value) {
    const code = ch.codePointAt(0) ?? 0;
    if (code >= 0x20 && code !== 0x7f) out += ch;
  }
  return out;
}

/** iTerm2 proprietary inline image (remote URL fetched by terminal). */
export function iterm2InlineImage(url: string, alt?: string): string {
  const safeUrl = stripControlChars(url);
  const label = alt?.trim() ? `\n${alt.trim()}\n` : "\n";
  return `${label}\x1b]1337;File=inline=1;width=auto;height=auto;preserveAspectRatio=1:url=${safeUrl}\x07`;
}

/** Kitty placeholder: show caption + URL (full graphics need icat binary). */
export function kittyImageFallback(url: string, alt?: string): string {
  const caption = alt?.trim() || "Image";
  return `\n${caption}\n  ${url}\n`;
}

export function replaceMarkdownImages(markdown: string, caps: TerminalCapabilities): string {
  if (!caps.iterm2InlineImages && !caps.kittyTerminal) return markdown;

  return markdown.replace(IMAGE_MD, (_full, alt: string, url: string) => {
    if (caps.iterm2InlineImages) return iterm2InlineImage(url, alt);
    if (caps.kittyTerminal) return kittyImageFallback(url, alt);
    return _full;
  });
}
