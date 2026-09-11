"""Install listen.wav + storms.mp3 next to the package. Personal-use audio."""
from __future__ import annotations

import base64
import ssl
import urllib.request
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent
RAW = "https://raw.githubusercontent.com/Memberoffoxhound/FndZlda/main/fndzlda/"
TARGETS = ("listen.wav", "storms.mp3")
ALIASES = {
    "listen.wav": ("LockChime.wav", "listen.wav"),
    "storms.mp3": ("song-of-storms-ocarina.mp3", "storms.mp3"),
}


def _ok(path: Path) -> bool:
    try:
        return path.is_file() and path.stat().st_size > 200
    except OSError:
        return False


def _get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "FndZlda", "Accept": "*/*"})
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=20, context=ctx) as resp:
        return resp.read()


def _decode_sidecars(dest: Path) -> bool:
    parts = sorted(PACKAGE.glob(dest.name + ".b64*"))
    if not parts:
        return False
    blob = "".join(p.read_text(encoding="ascii", errors="ignore") for p in parts)
    blob = "".join(blob.split())
    if not blob:
        return False
    try:
        data = base64.b64decode(blob)
    except Exception:
        return False
    if len(data) < 200:
        return False
    dest.write_bytes(data)
    return True


def _copy_alias(dest: Path) -> bool:
    for name in ALIASES.get(dest.name, ()):    
        src = PACKAGE / name
        if _ok(src) and src.resolve() != dest.resolve():
            dest.write_bytes(src.read_bytes())
            return True
    return False


def _download(dest: Path) -> bool:
    for name in (dest.name, dest.name + ".b64") + ALIASES.get(dest.name, ()):
        try:
            data = _get(RAW + name)
        except Exception:
            continue
        if name.endswith(".b64"):
            try:
                data = base64.b64decode(b"".join(data.split()))
            except Exception:
                continue
        if len(data) < 200:
            continue
        dest.write_bytes(data)
        return True
    return False


def ensure_sounds(package: Path | None = None) -> list[str]:
    """Make sure listen.wav and storms.mp3 exist. Returns names that were installed."""
    pkg = package or PACKAGE
    got: list[str] = []
    for name in TARGETS:
        dest = pkg / name
        if _ok(dest):
            continue
        if _copy_alias(dest) or _decode_sidecars(dest) or _download(dest):
            got.append(name)
    return got
