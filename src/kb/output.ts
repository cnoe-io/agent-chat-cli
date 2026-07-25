/**
 * KB commands always emit JSON (AWS CLI style).
 */

export function writeKbJson(data: unknown): void {
  process.stdout.write(`${JSON.stringify(data, null, 2)}\n`);
}

export function writeKbError(err: unknown): never {
  if (err && typeof err === "object" && "name" in err && err.name === "KbApiError") {
    const e = err as { message: string; status: number; body?: unknown };
    process.stderr.write(
      `${JSON.stringify({ error: e.message, status: e.status, body: e.body ?? null }, null, 2)}\n`,
    );
    process.exit(1);
  }
  const message = err instanceof Error ? err.message : String(err);
  process.stderr.write(`${JSON.stringify({ error: message }, null, 2)}\n`);
  process.exit(1);
}
