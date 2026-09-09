"""Beep / desktop ping on a hit. Never required for the hunt to work."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path


def ping(title: str, body: str) -> None:
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
        try:
            subprocess.Popen(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    f"[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null; "
                    f"Write-Host {body!r}",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            pass
        return
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
    """Post a stock alert to Discord via webhook. Returns True if sent."""
    url = _webhook_url()
    if not url:
        return False
    lines = [body]
    if price is not None:
        lines.append(f"Price: ${price:.2f}")
    if product_url:
        lines.append(f"Product: {product_url}")
    if cart_url:
        lines.append(f"Add to cart: {cart_url}")
    if checkout_url:
        lines.append(f"Checkout / buy: {checkout_url}")
    content = f"**{title}**\n" + "\n".join(lines)
    payload = json.dumps({"content": content[:1900], "username": "FndZlda"}).encode("utf-8")
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
