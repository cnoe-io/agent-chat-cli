/**
 * Alternate screen buffer and viewport control for full-terminal chat UI.
 */

let alternateActive = false;

export function isAlternateScreenActive(): boolean {
  return alternateActive;
}

/** Enter xterm alternate screen (1049). */
export function enterAlternateScreen(): void {
  if (alternateActive || !process.stdout.isTTY) return;
  process.stdout.write("\x1b[?1049h");
  alternateActive = true;
}

/** Leave alternate screen and restore main scrollback. */
export function leaveAlternateScreen(): void {
  if (!alternateActive) return;
  process.stdout.write("\x1b[?1049l");
  alternateActive = false;
}

/** Clear visible viewport (works in alternate or main buffer). */
export function clearViewport(): void {
  if (!process.stdout.isTTY) return;
  process.stdout.write("\x1b[H\x1b[2J");
}

/** Ensure alternate screen is released on exit signals. */
export function installAlternateScreenCleanup(): void {
  const cleanup = () => {
    leaveAlternateScreen();
  };
  process.once("exit", cleanup);
  process.once("SIGINT", () => {
    cleanup();
  });
  process.once("SIGTERM", cleanup);
}
