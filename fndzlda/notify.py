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
STORM_NAMES = ("storms.mp3", "storms.wav", "song-of-storms-ocarina.mp3")
RAW = "https://raw.githubusercontent.com/Memberoffoxhound/FndZlda/main/fndzlda/"


def _candidates(name: str) -> list[Path]:
    out: list[Path] = []
    env_map = {
        "listen.wav": "FNDZLDA_CHIME",
        "storms.mp3": "FNDZLDA_THEME",
        "storms.wav": "FNDZLDA_THEME",
    }
    env = (os.environ.get(env_map.get(name, "")) or "").strip()
    if env:
        out.append(Path(env))
    local = os.environ.get("LOCALAPPDATA")
    if local:
        out.append(Path(local) / "FndZlda" / name)
        out.append(Path(local) / "FndZlda" / "app" / "fndzlda" / name)
    out.append(_DIR / name)
    home = Path.home() / ".fndzlda" / name
    out.append(home)
    return out


def _ok_file(path: Path) -> bool:
    try:
        return path.is_file() and path.stat().st_size > 200
    except OSError:
        return False


def _download(url: str, dest: Path) -> bool:
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 FndZlda",
                "Accept": "*/*",
            },
        )
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            blob = resp.read()
        if len(blob) < 200:
            return False
        dest.write_bytes(blob)
        return True
    except Exception:
        return False


def ensure_sound(name: str) -> Path | None:
    for path in _candidates(name):
        if _ok_file(path):
            return path
    dest = _DIR / name
    if _download(RAW + name, dest):
        return dest
    local = os.environ.get("LOCALAPPDATA")
    if local:
        alt = Path(local) / "FndZlda" / name
        if _download(RAW + name, alt):
            return alt
    return None


def _play_win(path: Path) -> bool:
    full = str(path.resolve())
    if path.suffix.lower() == ".wav":
        try:
            import winsound

            winsound.PlaySound(full, winsound.SND_FILENAME | winsound.SND_ASYNC)
            return True
        except Exception:
            pass
    # wmplayer can do mp3 without a visible window most of the time
    wm = shutil.which("wmplayer") or r"C:\Program Files\Windows Media Player\wmplayer.exe"
    if Path(wm).is_file():
        try:
            subprocess.Popen(
                [wm, "/play", "/close", full],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        except Exception:
            pass
    uri = Path(full).as_uri()
    ps = (
        "Add-Type -AssemblyName presentationCore; "
        "$p = New-Object System.Windows.Media.MediaPlayer; "
        f"$p.Open([Uri]'{uri}'); $p.Volume = 1; $p.Play(); "
        "Start-Sleep -Seconds 6"
    )
    try:
        subprocess.Popen(
            ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except Exception:
        return False


def _play_unix(path: Path) -> bool:
    if sys.platform == "darwin":
        cmd = ["afplay", str(path)]
    else:
        cmd = None
        for bin_name in ("ffplay", "mpv", "mpg123", "paplay", "aplay"):
            if shutil.which(bin_name):
                if bin_name == "ffplay":
                    cmd = [bin_name, "-nodisp", "-autoexit", "-loglevel", "quiet", str(path)]
                elif bin_name == "mpv":
                    cmd = [bin_name, "--no-video", "--really-quiet", str(path)]
                else:
                    cmd = [bin_name, str(path)]
                break
        if cmd is None:
            return False
    try:
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False


def _play_path(path: Path) -> bool:
    if sys.platform == "win32":
        return _play_win(path)
    return _play_unix(path)


def play_chime() -> None:
    def _run() -> None:
        path = ensure_sound(CHIME_NAME)
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
    path = None
    for name in STORM_NAMES:
        path = ensure_sound(name)
        if path is not None:
            break
    if path is None:
        print("  theme    missing — put storms.mp3 in %LOCALAPPDATA%\\FndZlda or the repo")
        return
    ok = _play_path(path)
    if ok:
        print(f"  theme    Song of Storms  ({path.name})")
    else:
        print(f"  theme    found {path.name} but the player failed")


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
    lines = [f"**{title}**", f"**{body}**"]
    if price is not None:
        lines.append(f"${price:.2f}")
    lines.append("")
    if checkout_url:
        lines.append("**BUY / CHECKOUT**")
        lines.append(checkout_url)
        lines.append("")
    if cart_url and cart_url != checkout_url:
        lines.append("**ADD TO CART**")
        lines.append(cart_url)
        lines.append("")
    if product_url and product_url not in (cart_url, checkout_url):
        lines.append("**PRODUCT PAGE**")
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
