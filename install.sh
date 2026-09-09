#!/usr/bin/env bash
# One-step Linux / macOS install. No extra packages. US hunter.
# Stock macOS ships bash 3.2 — keep this script free of bash 4 features.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"

if ! command -v python3 >/dev/null 2>&1; then
  echo "FndZlda needs Python 3.10 or newer (the python3 command)."
  echo "macOS:            brew install python"
  echo "                  or https://www.python.org/downloads/"
  echo "SteamOS / Arch:   sudo pacman -S python"
  echo "Debian / Ubuntu:  sudo apt install python3"
  exit 1
fi
if ! python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)'; then
  echo "FndZlda needs Python 3.10 or newer. This is: $(python3 --version 2>&1)"
  exit 1
fi

BIN="${HOME}/.local/bin"
SHARE="${HOME}/.local/share/fndzlda"
mkdir -p "$BIN" "$SHARE"
rm -rf "$SHARE/fndzlda"
cp -R "$ROOT/fndzlda" "$SHARE/"
cp -R "$ROOT/fndzlda.sh" "$SHARE/" 2>/dev/null || true
if command -v git >/dev/null 2>&1 && git -C "$ROOT" rev-parse HEAD >/dev/null 2>&1; then
  git -C "$ROOT" rev-parse HEAD > "$SHARE/fndzlda/.commit"
fi

# Quote the path in the wrapper so spaces in a macOS user name are fine.
cat > "$BIN/fndzlda" <<EOF
#!/usr/bin/env bash
export PYTHONPATH="${SHARE}"
exec python3 -m fndzlda "\$@"
EOF
chmod +x "$BIN/fndzlda" "$ROOT/fndzlda.sh"

echo
echo "  Installed."
echo "  Run:  fndzlda"
if [[ ":$PATH:" != *":$BIN:"* ]]; then
  echo
  echo "  PATH does not include $BIN yet. Either:"
  echo "    export PATH=\"\$HOME/.local/bin:\$PATH\""
  echo "  or run:"
  echo "    $BIN/fndzlda"
fi
echo
echo "  First launch asks: console, Zelda Pro Controller, or both."
echo
read -r -p "  Start it now? [Y/n] " ans
ans="${ans:-Y}"
if [[ "$ans" =~ ^[Yy]$ ]]; then
  exec "$BIN/fndzlda"
fi
