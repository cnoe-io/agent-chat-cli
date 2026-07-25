#!/usr/bin/env node
/**
 * Installed caipe command (~/.local/bin/caipe from install.sh).
 * Prefers a dev checkout (Node/tsx); else runs the release binary from ~/.local/share/caipe.
 */
"use strict";

const { spawnSync } = require("node:child_process");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");

const args = process.argv.slice(2);

function exists(p) {
  try {
    return fs.existsSync(p);
  } catch {
    return false;
  }
}

function findDevLauncher() {
  const home = os.homedir();
  const roots = [
    process.env.CAIPE_CLI_ROOT,
    path.join(home, "outshift/caipe-cli"),
    path.join(home, "src/caipe-cli"),
    path.join(home, "git/caipe-cli"),
  ].filter(Boolean);

  for (const root of roots) {
    const launcher = path.join(path.resolve(root), "bin/caipe.cjs");
    if (exists(launcher)) return launcher;
  }
  return null;
}

function shareBinary() {
  const share = process.env.CAIPE_SHARE_DIR || path.join(os.homedir(), ".local/share/caipe");
  const platform = `${process.platform === "darwin" ? "darwin" : "linux"}-${process.arch === "arm64" ? "arm64" : "x64"}`;
  const bin = path.join(share, `caipe-${platform}`);
  return exists(bin) ? bin : null;
}

function run(bin, binArgs) {
  const r = spawnSync(bin, binArgs, { stdio: "inherit" });
  if (r.error) {
    process.stderr.write(`[caipe] ${r.error.message}\n`);
    process.exit(1);
  }
  return r;
}

const dev = findDevLauncher();
if (dev) {
  const r = run(process.execPath, [dev, ...args]);
  process.exit(r.status ?? (r.signal ? 128 : 1));
}

const released = shareBinary();
if (released) {
  const r = run(released, args);
  if (r.signal === "SIGKILL" || r.status === 137) {
    process.stderr.write(
      "[caipe] Binary was killed (signal 9). Clone caipe-cli, run `npm run link:path`, or set CAIPE_CLI_ROOT.\n",
    );
  }
  process.exit(r.status ?? (r.signal ? 128 : 1));
}

process.stderr.write(
  "[caipe] Not installed. Run install.sh or clone caipe-cli and `npm run link:path`.\n",
);
process.exit(1);
