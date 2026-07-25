#!/usr/bin/env node
/**
 * PATH stub for ~/.local/bin/caipe (copy or install.sh — do not symlink the repo caipe.cjs here).
 * Finds your caipe-cli checkout and runs bin/caipe.cjs (Node/tsx), not the Bun binary.
 */
"use strict";

const { spawnSync } = require("node:child_process");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");

function exists(p) {
  try {
    return fs.existsSync(p);
  } catch {
    return false;
  }
}

function resolveRepoRoot() {
  if (process.env.CAIPE_CLI_ROOT) {
    return path.resolve(process.env.CAIPE_CLI_ROOT);
  }

  const home = os.homedir();
  const candidates = [
    path.join(home, "outshift/caipe-cli"),
    path.join(home, "src/caipe-cli"),
    path.join(home, "git/caipe-cli"),
    path.join(home, "projects/caipe-cli"),
  ];

  for (const dir of candidates) {
    const launcher = path.join(dir, "bin/caipe.cjs");
    if (exists(launcher)) return dir;
  }

  return null;
}

const root = resolveRepoRoot();
if (!root) {
  process.stderr.write(
    "[caipe] No caipe-cli checkout found. Clone the repo and set:\n" +
      "  export CAIPE_CLI_ROOT=/path/to/caipe-cli\n" +
      "Or run: npm run link:path   (from the caipe-cli repo)\n",
  );
  process.exit(1);
}

const launcher = path.join(root, "bin/caipe.cjs");
const args = process.argv.slice(2);
const r = spawnSync(process.execPath, [launcher, ...args], {
  stdio: "inherit",
  env: { ...process.env, CAIPE_CLI_ROOT: root },
});

if (r.error) {
  process.stderr.write(`[caipe] ${r.error.message}\n`);
  process.exit(1);
}
process.exit(r.status ?? (r.signal ? 128 : 1));
