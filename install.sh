#!/usr/bin/env bash
# One-step Linux install. No extra packages. US hunter.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"

if ! command -v python3 >/dev/null 2>&1; then
  echo "FndZlda needs python3."
  echo "SteamOS / Arch:  sudo pacman -S python"
  echo "Debian / Ubuntu: sudo apt install python3"
  exit 1
fi

BIN="${HOME}/.local/bin"
SHARE="${HOME}/.local/share/fndzlda"
mkdir -p "$BIN" "$SHARE"
rm -rf "$SHARE/fndzlda"
cp -a "$ROOT/fndzlda" "$SHARE/"
cp -a "$ROOT/fndzlda.sh" "$SHARE/" 2>/dev/null || true

cat > "$BIN/fndzlda" <<EOF
#!/usr/bin/env bash
export PYTHONPATH=${SHARE@Q}
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
