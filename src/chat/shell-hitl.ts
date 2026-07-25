/**
 * Human-in-the-loop gate for local shell execution (`! cmd` and `| pipe`).
 */

export type ShellApprovalKind = "escape" | "pipe";

export interface ShellApprovalRequest {
  cmd: string;
  kind: ShellApprovalKind;
}

/** When true, skip the approval prompt (non-interactive / trusted sessions). */
export function isShellHitlEnabled(): boolean {
  const auto = process.env.CAIPE_SHELL_AUTO_APPROVE;
  if (auto === "1" || auto === "true" || auto === "yes") return false;
  const hitl = process.env.CAIPE_HITL_SHELL;
  if (hitl === "0" || hitl === "false" || hitl === "no") return false;
  return true;
}

export function shellApprovalTitle(kind: ShellApprovalKind): string {
  return kind === "escape" ? "Run local shell command?" : "Pipe response through shell?";
}
