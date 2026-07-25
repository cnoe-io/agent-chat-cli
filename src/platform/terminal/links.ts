/**
 * OSC 8 hyperlinks for terminals that support clickable links.
 */

const OSC8_OPEN = "\x1b]8;;";
const OSC8_CLOSE = "\x1b]8;;\x1b\\";

function stripControlChars(value: string): string {
  let out = "";
  for (const ch of value) {
    const code = ch.codePointAt(0) ?? 0;
    if (code >= 0x20 && code !== 0x7f) out += ch;
  }
  return out;
}

export function osc8Hyperlink(url: string, label: string): string {
  const safeUrl = stripControlChars(url);
  const safeLabel = label || safeUrl;
  return `${OSC8_OPEN}${safeUrl}${OSC8_CLOSE}${safeLabel}${OSC8_CLOSE}`;
}

/** Replace markdown links with OSC 8 hyperlinks (before marked parse). */
export function replaceMarkdownLinksWithOsc8(markdown: string): string {
  return markdown.replace(
    /\[([^\]]+)\]\(([^)\s]+)(?:\s+"[^"]*")?\)/g,
    (_, label: string, url: string) => {
      if (url.startsWith("#")) return `[${label}](${url})`;
      return osc8Hyperlink(url, label);
    },
  );
}

/** Replace bare https URLs with OSC 8 (skip lines that already contain OSC 8). */
export function linkifyBareUrls(text: string): string {
  if (text.includes(OSC8_OPEN)) return text;
  return text.replace(/(?<![(\[])(https?:\/\/[^\s)\]>]+)/g, (url) => osc8Hyperlink(url, url));
}
