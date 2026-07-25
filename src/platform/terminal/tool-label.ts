/** Claude-style tool tree labels (Update(path), etc.). */

export function pathFromToolDetail(detail: string): string | undefined {
  const trimmed = detail.trim();
  if (!trimmed) return undefined;
  try {
    const obj = JSON.parse(trimmed) as Record<string, unknown>;
    for (const key of ["path", "file_path", "filePath", "filename"]) {
      const v = obj[key];
      if (typeof v === "string" && v.trim()) return v.trim();
    }
  } catch {
    /* plain command string */
  }
  return trimmed;
}

export function formatToolTreeLabel(name: string, detail?: string): string {
  const n = name.toLowerCase().replace(/[^a-z0-9_]/g, "_");
  const path = detail ? pathFromToolDetail(detail) : undefined;
  if (path && /write|edit|patch|update|replace|str_replace|file/.test(n)) {
    return `Update(${path})`;
  }
  if (path && (n.includes("bash") || n.includes("shell") || n.includes("terminal"))) {
    return path;
  }
  if (path) return `${name}(${path})`;
  return name;
}
