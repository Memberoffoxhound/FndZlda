"""Startup art: cave old man, Master Sword, plus the Ocarina wordmark."""
from __future__ import annotations

import os
import sys

from fndzlda.scene import disappointment, hey_listen, render_intro

GOLD = "\033[38;5;220m"
GOLD2 = "\033[38;5;178m"
GOLD_BRIGHT = "\033[1;38;5;227m"
CYAN = "\033[1;38;5;87m"
DIM = "\033[38;5;94m"
RESET = "\033[0m"


def enable_windows_ansi() -> None:
    if sys.platform != "win32":
        return
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)
        mode = ctypes.c_uint()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            kernel32.SetConsoleMode(handle, mode.value | 0x0004)
        kernel32.SetConsoleOutputCP(65001)
    except Exception:
        pass


def _use_color() -> bool:
    if os.environ.get("NO_COLOR") or os.environ.get("FNDZLDA_PLAIN"):
        return False
    try:
        return sys.stdout.isatty()
    except Exception:
        return False


def _use_unicode() -> bool:
    enc = (getattr(sys.stdout, "encoding", None) or "").lower()
    return "utf" in enc or sys.platform != "win32"


def render(color: bool | None = None, unicode: bool | None = None) -> str:
    extra = (
        "              T H E   L E G E N D   O F\n"
        "              ~  O C A R I N A   O F   T I M E  ~\n"
        "                         /\\\n"
        "                      /______\\\n"
        "         ZZZZZ  EEEEE\n"
        "                   1998  Nintendo\n"
        "              FndZlda\n"
    )
    body = render_intro(color=False) + extra
    use_color = color if color is not None else _use_color()
    if use_color:
        return GOLD + body + RESET
    return body


def print_logo() -> None:
    enable_windows_ansi()
    sys.stdout.write(render_intro())
    sys.stdout.flush()
