/**
 * Terminal feature detection for rich CLI output (hyperlinks, images, alt screen).
 */

export interface TerminalCapabilities {
  /** 256 / truecolor ANSI available */
  trueColor: boolean;
  /** OSC 8 clickable hyperlinks (iTerm2, Kitty, WezTerm, modern VTE) */
  osc8Links: boolean;
  /** iTerm2 inline image protocol (File=…;url=…) */
  iterm2InlineImages: boolean;
  /** Kitty terminal (limited inline image support without icat) */
  kittyTerminal: boolean;
  /** Use alternate screen buffer for full-session TUI */
  alternateScreen: boolean;
  /** Usable terminal width for markdown reflow */
  width: number;
}

function envDisabled(name: string): boolean {
  const v = process.env[name];
  return v === "1" || v === "true" || v === "yes";
}

function terminalProgram(): string {
  return (process.env.TERM_PROGRAM ?? "").toLowerCase();
}

function colorTerm(): string {
  return (process.env.COLORTERM ?? "").toLowerCase();
}

/** Rich output enabled (respects NO_COLOR and CAIPE_PLAIN_TERMINAL). */
export function isRichTerminalEnabled(): boolean {
  if (process.env.NO_COLOR) return false;
  if (envDisabled("CAIPE_PLAIN_TERMINAL")) return false;
  return Boolean(process.stdout.isTTY);
}

export function getTerminalWidth(fallback = 80): number {
  const cols = process.stdout.columns;
  if (typeof cols === "number" && cols >= 20) return cols;
  return fallback;
}

/** Horizontal inset for Ink message rows (paddingX + optional prompt glyph). */
export type MarkdownLayoutVariant = "assistant" | "user" | "full";

/**
 * Column width for markdown / tables inside the REPL.
 * Must match the Ink box that hosts {@link AnsiBlock} or tables spill and ANSI breaks.
 */
export function getMarkdownLayoutWidth(variant: MarkdownLayoutVariant = "assistant"): number {
  const cols = getTerminalWidth();
  let inset = 2; // paddingX={1} on message rows
  if (variant === "assistant") {
    inset += 2; // body indent under ⏺ (column layout)
  } else if (variant === "user") {
    inset += 2; // "❯ " prefix
  }
  return Math.max(20, cols - inset);
}

/**
 * Detect terminal capabilities once per process (re-call after SIGWINCH if needed).
 */
export function getTerminalCapabilities(): TerminalCapabilities {
  const rich = isRichTerminalEnabled();
  const width = getTerminalWidth();
  const term = (process.env.TERM ?? "").toLowerCase();
  const program = terminalProgram();

  const iterm2 = program.includes("iterm") || program === "iterm.app";
  const kitty = program === "kitty" || term.includes("kitty");
  const wez = program.includes("wezterm");
  const ghostty = program.includes("ghostty");
  const vteModern = term.includes("xterm") || term.includes("alacritty") || term.includes("foot");

  const colorenv = colorTerm();

  const trueColor =
    rich &&
    (colorenv.includes("truecolor") ||
      colorenv.includes("24bit") ||
      iterm2 ||
      kitty ||
      wez ||
      ghostty);

  const osc8Links = rich && (iterm2 || kitty || wez || ghostty || vteModern);

  const iterm2InlineImages = rich && iterm2 && !envDisabled("CAIPE_NO_INLINE_IMAGES");

  const alternateScreen =
    rich &&
    Boolean(process.stdout.isTTY) &&
    !envDisabled("CAIPE_NO_ALT_SCREEN") &&
    !envDisabled("CAIPE_PLAIN_TERMINAL");

  return {
    trueColor,
    osc8Links,
    iterm2InlineImages,
    kittyTerminal: rich && kitty,
    alternateScreen,
    width,
  };
}
