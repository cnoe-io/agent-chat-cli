#!/usr/bin/env sh
# Install ~/.local/bin/caipe as a Node stub (not the 62MB Bun binary).
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="${CAIPE_INSTALL_DIR:-$HOME/.local/bin}/caipe"
mkdir -p "$(dirname "$DEST")"
cp "$ROOT/bin/caipe-path.cjs" "$DEST"
chmod +x "$DEST"
# Remove stale Mach-O binary if present
if file "$DEST" 2>/dev/null | grep -q Mach-O; then
  : # cp already replaced
fi
echo "Installed Node launcher to $DEST (uses checkout at \$CAIPE_CLI_ROOT or ~/outshift/caipe-cli)"
"$DEST" --version
