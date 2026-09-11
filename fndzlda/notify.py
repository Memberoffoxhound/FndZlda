"""Beep / desktop ping / Navi chime on a hit. Never required for the hunt to work."""
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
CHIME_URL = (
    "https://raw.githubusercontent.com/Memberoffoxhound/FndZlda/main/fndzlda/listen.wav"
)


def _chime_path() -> Path:
    env = (os.environ.get("FNDZLDA_CHIME") or "").strip()
    if env:
        return Path(env)
    local = os.environ.get("LOCALAPPDATA")
    if local:
        extra = Path(local) / "FndZlda" / CHIME_NAME
        if extra.is_file() and extra.stat().st_size > 100:
            return extra
    return _DIR / CHIME_NAME


def _download_chime(dest: Path) -> bool:
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(CHIME_URL, headers={"User-Agent": "FndZlda"})
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=12, context=ctx) as resp:
            blob = resp.read()
        if len(blob) < 100 or blob[:4] != b"RIFF":
            return False
        dest.write_bytes(blob)
        return True
    except Exception:
        return False


def ensure_chime() -> Path | None:
    path = _chime_path()
    if path.is_file() and path.stat().st_size > 100:
        return path
    pkg = _DIR / CHIME_NAME
    if _download_chime(pkg):
        return pkg
    return None


def play_chime() -> None:
    """Play listen.wav in the background. Falls back to a short beep."""

    def _run() -> None:
        path = ensure_chime()
        if path is not None and sys.platform == "win32":
            try:
                import winsound

                winsound.PlaySound(
                    str(path),
                    winsound.SND_FILENAME | winsound.SND_ASYNC,
                )
                return
            except Exception:
                pass
        if path is not None:
            player = None
            if sys.platform == "darwin":
                player = ["afplay", str(path)]
            else:
                for bin_name in ("paplay", "aplay", "ffplay"):
                    if shutil.which(bin_name):
                        if bin_name == "ffplay":
                            player = [bin_name, "-nodisp", "-autoexit", "-loglevel", "quiet", str(path)]
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
                    return
                except Exception:
                    pass
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
