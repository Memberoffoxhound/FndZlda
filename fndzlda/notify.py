"""Beep / desktop ping / Navi chime / hunt theme. Never required for the hunt to work."""
from __future__ import annotations

import json
import os
import shutil
import ssl
import subprocess
import sys
import threading
import urllib.request
from pathlib import Path

_DIR = Path(__file__).resolve().parent
CHIME_NAME = "listen.wav"
STORM_NAME = "storms.mp3"
RAW = "https://raw.githubusercontent.com/Memberoffoxhound/FndZlda/main/fndzlda/"


def _localapp(name: str) -> Path | None:
    local = os.environ.get("LOCALAPPDATA")
    if not local:
        return None
    extra = Path(local) / "FndZlda" / name
    if extra.is_file() and extra.stat().st_size > 100:
        return extra
    return None


def _download(url: str, dest: Path, magic: bytes | None = None) -> bool:
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(url, headers={"User-Agent": "FndZlda"})
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=12, context=ctx) as resp:
            blob = resp.read()
        if len(blob) < 100:
            return False
        if magic and not blob.startswith(magic):
            return False
        dest.write_bytes(blob)
        return True
    except Exception:
        return False


def ensure_sound(name: str, env_key: str = "") -> Path | None:
    if env_key:
        env = (os.environ.get(env_key) or "").strip()
        if env:
            p = Path(env)
            if p.is_file():
                return p
    extra = _localapp(name)
    if extra is not None:
        return extra
    pkg = _DIR / name
    if pkg.is_file() and pkg.stat().st_size > 100:
        return pkg
    magic = b"RIFF" if name.endswith(".wav") else None
    if _download(RAW + name, pkg, magic=magic):
        return pkg
    return None


def _play_path(path: Path) -> bool:
    suffix = path.suffix.lower()
    if sys.platform == "win32" and suffix == ".wav":
        try:
            import winsound

            winsound.PlaySound(str(path), winsound.SND_FILENAME | winsound.SND_ASYNC)
            return True
        except Exception:
            pass
    if sys.platform == "win32":
        ps = (
            "Add-Type -AssemblyName presentationCore; "
            "$p = New-Object System.Windows.Media.MediaPlayer; "
            f"$p.Open([uri]{(str(path.resolve()))!r}); "
            "$p.Play(); Start-Sleep -Seconds 6"
        )
        try:
            subprocess.Popen(
                ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        except Exception:
            pass
    if sys.platform == "darwin":
        player = ["afplay", str(path)]
    else:
        player = None
        for bin_name in ("ffplay", "paplay", "aplay", "mpg123", "mpv"):
            if shutil.which(bin_name):
                if bin_name == "ffplay":
                    player = [bin_name, "-nodisp", "-autoexit", "-loglevel", "quiet", str(path)]
                elif bin_name == "mpv":
                    player = [bin_name, "--no-video", "--really-quiet", str(path)]
                else:
                    player = [bin_name, str(path)]
                break
    if player:
        try:
            subprocess.Popen(
                player,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        except Exception:
            return False
    return False


def play_chime() -> None:
    def _run() -> None:
        path = ensure_sound(CHIME_NAME, "FNDZLDA_CHIME")
        if path is not None and _play_path(path):
            return
        try:
            sys.stdout.write("\a")
            sys.stdout.flush()
        except Exception:
            pass
        if sys.platform == "win32":
            try:
                import winsound

                winsound.Beep(880, 180)
                winsound.Beep(1175, 220)
            except Exception:
                pass

    threading.Thread(target=_run, daemon=True).start()


def play_hunt_theme() -> None:
    """Song of Storms when the hunt actually starts."""

    def _run() -> None:
        path = ensure_sound(STORM_NAME, "FNDZLDA_THEME")
        if path is not None:
            _play_path(path)

    threading.Thread(target=_run, daemon=True).start()


def ping(title: str, body: str) -> None:
    play_chime()
    if shutil.which("notify-send"):
        try:
            subprocess.Popen(
                ["notify-send", "--app-name=FndZlda", title, body],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            pass
    elif sys.platform == "darwin":
        try:
            subprocess.Popen(
                ["osascript", "-e", f'display notification {body!r} with title {title!r}'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            pass


def _webhook_url() -> str:
    env = (os.environ.get("DISCORD_WEBHOOK_URL") or "").strip()
    if env:
        return env
    cfg = Path.home() / ".config" / "fndzlda" / "discord_webhook.env"
    if cfg.is_file():
        for line in cfg.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("DISCORD_WEBHOOK_URL="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def discord_stock(
    title: str,
    body: str,
    *,
    product_url: str = "",
    cart_url: str = "",
    checkout_url: str = "",
    price: float | None = None,
) -> bool:
    url = _webhook_url()
    if not url:
        return False

    lines = [
        f"**{title}**",
        f"**{body}**",
    ]
    if price is not None:
        lines.append(f"${price:.2f}")
    lines.append("")
    if checkout_url:
        lines.append(f"**BUY / CHECKOUT**")
        lines.append(checkout_url)
        lines.append("")
    if cart_url and cart_url != checkout_url:
        lines.append(f"**ADD TO CART**")
        lines.append(cart_url)
        lines.append("")
    if product_url and product_url not in (cart_url, checkout_url):
        lines.append(f"**PRODUCT PAGE**")
        lines.append(product_url)

    content = "\n".join(lines).strip()[:1900]
    payload = json.dumps({"content": content, "username": "FndZlda"}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json", "User-Agent": "FndZlda/1.1"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            return 200 <= int(resp.status) < 300
    except Exception:
        return False
