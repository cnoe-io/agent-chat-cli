/**
 * marked-terminal list renderer + marked v15: list items keep raw `**` because
 * inline tokens live under a nested `text` token. Override `list` only.
 */

import type { MarkedExtension, Parser } from "marked";

type InlineCapable = { type: string; tokens?: InlineCapable[] };
type ListItemToken = { loose?: boolean; tokens?: InlineCapable[] };
type ListToken = { ordered?: boolean; start?: number | string; items: ListItemToken[] };

function listItemInlineText(parser: Parser, item: ListItemToken): string {
  const parts = item.tokens ?? [];
  if (parts.length === 0) return "";

  if (item.loose) {
    return parser.parse(parts).trimEnd();
  }

  if (parts.length === 1) {
    const head = parts[0];
    if (head?.type === "paragraph" && head.tokens?.length) {
      return parser.parseInline(head.tokens).trim();
    }
    if (head?.type === "text" && head.tokens?.length) {
      return parser.parseInline(head.tokens).trim();
    }
  }

  return parser.parseInline(parts).trim();
}

export function markedListInlineExtension(): MarkedExtension {
  return {
    name: "caipe-list-inline",
    renderer: {
      list(token) {
        const listToken = token as ListToken;
        let index = listToken.start ? Number(listToken.start) : 1;
        const lines = listToken.items.map((item) => {
          const content = listItemInlineText(this.parser, item);
          const prefix = listToken.ordered ? `${index++}. ` : "• ";
          return prefix + content;
        });
        return `${lines.join("\n")}\n\n`;
      },
    },
  };
}
