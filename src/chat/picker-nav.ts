/** Shared keyboard list navigation for REPL pickers (slash commands, agents, …). */

export const PICKER_PAGE_JUMP = 5;
export const SLASH_PICKER_VISIBLE = 12;

export function pickerWindow(
  total: number,
  selectedIndex: number,
  visibleCount: number,
): { start: number; end: number } {
  if (total <= visibleCount) return { start: 0, end: total };
  const half = Math.floor(visibleCount / 2);
  let start = Math.max(0, selectedIndex - half);
  const end = Math.min(total, start + visibleCount);
  start = Math.max(0, end - visibleCount);
  return { start, end };
}

export function movePickerIndex(current: number, total: number, delta: number): number {
  if (total <= 0) return 0;
  const next = current + delta;
  if (next < 0) return total - 1;
  if (next >= total) return 0;
  return next;
}

export function pagePickerIndex(
  current: number,
  total: number,
  pageSize: number,
  direction: -1 | 1,
): number {
  if (total <= 0) return 0;
  const jump = pageSize * direction;
  const next = current + jump;
  if (next < 0) return 0;
  if (next >= total) return total - 1;
  return next;
}

export function clampPickerIndex(index: number, total: number): number {
  if (total <= 0) return 0;
  return Math.max(0, Math.min(index, total - 1));
}
