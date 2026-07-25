/** Best-effort shell command extraction from streaming tool-call JSON args. */

export function commandFromToolArgsBuffer(buffer: string): string | undefined {
  const trimmed = buffer.trim();
  if (!trimmed) return undefined;
  try {
    const obj = JSON.parse(trimmed) as Record<string, unknown>;
    for (const key of ["command", "cmd", "script", "input", "code"]) {
      const v = obj[key];
      if (typeof v === "string" && v.trim()) return v.trim();
    }
  } catch {
    const m = trimmed.match(/"(?:command|cmd)"\s*:\s*"((?:\\.|[^"\\])*)"/);
    if (m?.[1]) {
      try {
        return JSON.parse(`"${m[1]}"`) as string;
      } catch {
        return m[1];
      }
    }
  }
  return undefined;
}
