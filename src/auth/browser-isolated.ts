/**
 * Isolated Chromium launch for OAuth — separate profile from the user's daily browser.
 *
 * Avoids overwriting BFF / Web UI session cookies when completing PKCE login.
 */

import { type ChildProcess, spawn } from "node:child_process";
import { existsSync, mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

export type AuthBrowserMode = "isolated" | "system";

export interface LoginBrowserModeOptions {
  /** Explicit CLI override (`--isolated` / `--system-browser`). */
  browser?: AuthBrowserMode;
}

/**
 * Resolve how to open the OAuth authorize URL.
 * Default: isolated Chromium when available (`CAIPE_AUTH_BROWSER=isolated`).
 */
export function resolveAuthBrowserMode(opts?: LoginBrowserModeOptions): AuthBrowserMode {
  const env = process.env.CAIPE_AUTH_BROWSER?.trim().toLowerCase();
  if (env === "system") return "system";
  if (env === "isolated") return "isolated";
  if (opts?.browser) return opts.browser;
  return "isolated";
}

/** Optional override: path to Chrome/Chromium/Edge binary. */
export function findChromiumExecutable(): string | null {
  const override = process.env.CAIPE_CHROMIUM_PATH?.trim();
  if (override && existsSync(override)) return override;

  const candidates: string[] = [];

  if (process.platform === "darwin") {
    candidates.push(
      "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
      "/Applications/Chromium.app/Contents/MacOS/Chromium",
      "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
      "/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary",
      "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    );
  } else if (process.platform === "win32") {
    const local = process.env.LOCALAPPDATA ?? "";
    const pf = process.env.ProgramFiles ?? "C:\\Program Files";
    const pf86 = process.env["ProgramFiles(x86)"] ?? "C:\\Program Files (x86)";
    candidates.push(
      join(local, "Google", "Chrome", "Application", "chrome.exe"),
      join(pf, "Google", "Chrome", "Application", "chrome.exe"),
      join(pf86, "Google", "Chrome", "Application", "chrome.exe"),
      join(pf, "Microsoft", "Edge", "Application", "msedge.exe"),
    );
  } else {
    candidates.push(
      "/usr/bin/google-chrome-stable",
      "/usr/bin/google-chrome",
      "/usr/bin/chromium",
      "/usr/bin/chromium-browser",
      "/snap/bin/chromium",
    );
  }

  for (const path of candidates) {
    if (path && existsSync(path)) return path;
  }
  return null;
}

/**
 * Open `url` in a disposable browser profile. Returns cleanup (kill process + delete profile).
 */
export async function launchIsolatedBrowser(executable: string, url: string): Promise<() => void> {
  const profileDir = mkdtempSync(join(tmpdir(), "caipe-oauth-"));
  const headless = process.env.CAIPE_AUTH_HEADLESS === "1";
  const args = [
    `--user-data-dir=${profileDir}`,
    "--no-first-run",
    "--no-default-browser-check",
    "--disable-sync",
    "--disable-background-networking",
    "--disable-extensions",
    "--disable-features=TranslateUI",
  ];
  if (headless) {
    args.push("--headless=new");
  }
  args.push(url);

  let child: ChildProcess;
  try {
    child = spawn(executable, args, {
      detached: false,
      stdio: "ignore",
      windowsHide: true,
    });
  } catch (err) {
    rmSync(profileDir, { recursive: true, force: true });
    throw err;
  }

  const cleanup = () => {
    try {
      if (child.pid && !child.killed) {
        if (process.platform === "win32") {
          spawn("taskkill", ["/pid", String(child.pid), "/t", "/f"], { stdio: "ignore" });
        } else {
          child.kill("SIGTERM");
        }
      }
    } catch {
      /* ignore */
    }
    try {
      rmSync(profileDir, { recursive: true, force: true });
    } catch {
      /* ignore */
    }
  };

  child.on("error", (err) => {
    if (process.env.CAIPE_AUTH_DEBUG === "1") {
      process.stderr.write(`[caipe-auth] Isolated browser error: ${err.message}\n`);
    }
  });

  await new Promise((r) => setTimeout(r, 400));
  return cleanup;
}
