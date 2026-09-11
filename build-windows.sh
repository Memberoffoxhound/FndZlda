#!/usr/bin/env bash
# Cross-compile FndZlda.exe (Windows amd64) from Linux.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
export PATH="${HOME}/.local/go/bin:${PATH}"
command -v go >/dev/null || { echo "need Go: put it on PATH or in ~/.local/go"; exit 1; }

PAY="$ROOT/installer/windows/payload/fndzlda"
rm -rf "$PAY"
mkdir -p "$PAY"
cp "$ROOT"/fndzlda/*.py "$PAY/"
cp "$ROOT"/fndzlda/*.txt "$PAY/" 2>/dev/null || true

mkdir -p "$ROOT/dist"
cd "$ROOT/installer/windows"
GOOS=windows GOARCH=amd64 CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o "$ROOT/dist/FndZlda.exe" .
echo "wrote $ROOT/dist/FndZlda.exe"
ls -lh "$ROOT/dist/FndZlda.exe"
