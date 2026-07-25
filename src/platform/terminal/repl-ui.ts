/**
 * REPL UI toggles (reduce full-terminal flicker in Ink).
 */

/** Animated spinners (80–250ms). Default off — set CAIPE_SPINNER=1 to enable. */
export function animatedWaitEnabled(): boolean {
  return process.env.CAIPE_SPINNER === "1";
}

/** How often to refresh elapsed time on the wait line (ms). */
export function waitStatusTickMs(): number {
  if (animatedWaitEnabled()) return 250;
  const raw = process.env.CAIPE_WAIT_TICK_MS;
  if (raw) {
    const n = Number.parseInt(raw, 10);
    if (Number.isFinite(n) && n >= 500) return n;
  }
  return 1000;
}

/** Max tool tree rows while streaming (live footer). */
export function maxLiveToolTreeRows(): number {
  const raw = process.env.CAIPE_TOOL_TREE_MAX;
  if (raw) {
    const n = Number.parseInt(raw, 10);
    if (Number.isFinite(n) && n >= 0) return n;
  }
  return 2;
}

/** Max tool tree rows in completed tool-activity blocks. */
export function maxStaticToolTreeRows(): number {
  const raw = process.env.CAIPE_TOOL_TREE_STATIC_MAX;
  if (raw) {
    const n = Number.parseInt(raw, 10);
    if (Number.isFinite(n) && n >= 0) return n;
  }
  return 6;
}
