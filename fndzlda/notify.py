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


def _in_console() -> bool:
    """Only play audio when this process owns a real terminal."""
    try:
        if sys.stdin.isatty() or sys.stdout.isatty() or sys.stderr.isatty():
            return True
    except Exception:
        pass
    if sys.platform == "win32":
        try:
            import ctypes

            return bool(ctypes.windll.kernel32.GetConsoleWindow())
        except Exception:
            return False
    return False


def _play_win(path: Path) -> bool:
    """Play inside this process. No PowerShell, no wmplayer, no extra window."""
    full = str(path.resolve())
    suffix = path.suffix.lower()
    if suffix == ".wav":
        try:
            import winsound

            winsound.PlaySound(full, winsound.SND_FILENAME | winsound.SND_ASYNC)
            return True
        except Exception:
            return False
    # MP3 via winmm MCI — same process, no helper app.
    try:
        import ctypes

        winmm = ctypes.windll.winmm
        alias = "fndzlda_media"
        winmm.mciSendStringW(f"close {alias}", None, 0, None)
        err = winmm.mciSendStringW(
            f'open "{full}" type mpegvideo alias {alias}', None, 0, None
        )
        if err:
            err = winmm.mciSendStringW(f'open "{full}" alias {alias}', None, 0, None)
        if err:
            return False
        err = winmm.mciSendStringW(f"play {alias}", None, 0, None)
        return err == 0
    except Exception:
        return False


def _play_unix(path: Path) -> bool:
    # Bell only — do not spawn ffplay/mpv/afplay.
    try:
        sys.stdout.write("\a")
        sys.stdout.flush()
    except Exception:
        pass
    return False


def _play_path(path: Path) -> bool:
    if not _in_console():
        return False
    if sys.platform == "win32":
        return _play_win(path)
    return _play_unix(path)


def _windows_notify_sound() -> bool:
    """Stock Windows notification sound, in-process. No extra app."""
    if sys.platform != "win32":
        return False
    try:
        import winsound
    except Exception:
        return False
    media = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Media"
    wavs = (
        "Windows Notify System Generic.wav",
        "Windows Notify.wav",
        "Windows Background.wav",
        "Windows Notify Messaging.wav",
        "Nudge.wav",
    )
    for name in wavs:
        path = media / name
        if path.is_file():
            try:
                winsound.PlaySound(str(path), winsound.SND_FILENAME | winsound.SND_ASYNC)
                return True
            except Exception:
                pass
    for alias in ("SystemNotification", "SystemAsterisk", "SystemExclamation", "SystemDefault"):
        try:
            winsound.PlaySound(alias, winsound.SND_ALIAS | winsound.SND_ASYNC)
            return True
        except Exception:
            pass
    try:
        winsound.MessageBeep(winsound.MB_ICONASTERISK)
        return True
    except Exception:
        return False


def play_chime() -> None:
    def _run() -> None:
        if not _in_console():
            return
        if _windows_notify_sound():
            return
        path = ensure_sound(CHIME_NAME)
        if path is not None and _play_path(path):
            return
        try:
            sys.stdout.write("\a")
            sys.stdout.flush()
        except Exception:
            pass

    threading.Thread(target=_run, daemon=True).start()


def play_hunt_theme() -> None:
    """Song of Storms when the hunt actually starts. Console process only."""
    if not _in_console():
        return
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
