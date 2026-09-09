"""Ocarina of Time title-screen art for the terminal.

Gold Triforce + the N64-era wordmark. Works on Linux and Windows 10+
(VT processing is enabled on Windows). Falls back to plain ASCII if the
console cannot do ANSI or Unicode.
"""
from __future__ import annotations

import os
import sys

GOLD = "\033[38;5;220m"
GOLD2 = "\033[38;5;178m"
GOLD_BRIGHT = "\033[1;38;5;227m"
CYAN = "\033[38;5;87m"
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
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FNDZLDA_PLAIN"):
        return False
    try:
        return sys.stdout.isatty()
    except Exception:
        return False


def _use_unicode() -> bool:
    enc = (getattr(sys.stdout, "encoding", None) or "").lower()
    return "utf" in enc or sys.platform != "win32"


TRIFORCE_UNI = r"""
                         /\
                        /  \
                       /    \
                      /______\
                     /\      /\
                    /  \    /  \
                   /    \  /    \
                  /______\/______\
"""

ZELDA_UNI = r"""
              T H E   L E G E N D   O F
        \u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2557\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2557\u2588\u2588\u2557     \u2588\u2588\u2588\u2588\u2588\u2588\u2557  \u2588\u2588\u2588\u2588\u2588\u2557
        \u255a\u2550\u2550\u2588\u2588\u2588\u2554\u255d\u2588\u2588\u2554\u2550\u2550\u2550\u2550\u255d\u2588\u2588\u2551     \u2588\u2588\u2554\u2550\u2550\u2588\u2588\u2557\u2588\u2588\u2554\u2550\u2550\u2588\u2588\u2557
          \u2588\u2588\u2588\u2554\u255d \u2588\u2588\u2588\u2588\u2588\u2557  \u2588\u2588\u2551     \u2588\u2588\u2551  \u2588\u2588\u2551\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2551
         \u2588\u2588\u2588\u2554\u255d  \u2588\u2588\u2554\u2550\u2550\u255d  \u2588\u2588\u2551     \u2588\u2588\u2551  \u2588\u2588\u2551\u2588\u2588\u2554\u2550\u2550\u2588\u2588\u2551
        \u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2557\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2557\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2557\u2588\u2588\u2588\u2588\u2588\u2588\u2554\u255d\u2588\u2588\u2551  \u2588\u2588\u2551
        \u255a\u2550\u2550\u2550\u2550\u2550\u2550\u255d\u255a\u2550\u2550\u2550\u2550\u2550\u2550\u255d\u255a\u2550\u2550\u2550\u2550\u2550\u2550\u255d\u255a\u2550\u2550\u2550\u2550\u255d \u255a\u2550\u255d  \u255a\u2550\u255d
"""

SUB_UNI = r"""
              ~  O C A R I N A   O F   T I M E  ~
"""

FOOT_UNI = """
                    *  .  *    .  *  .
                   \u00a9 1998  Nintendo
"""

TRIFORCE_ASCII = r"""
                         /\
                        /  \
                       /    \
                      /______\
                     /\      /\
                    /  \    /  \
                   /    \  /    \
                  /______\/______\
"""

ZELDA_ASCII = r"""
              T H E   L E G E N D   O F
         ZZZZZ  EEEEE  L      DDDD    AAA
            Z   E      L      D   D  A   A
           Z    EEEE   L      D   D  AAAAA
          Z     E      L      D   D  A   A
         ZZZZZ  EEEEE  LLLLL  DDDD   A   A
"""

SUB_ASCII = r"""
              ~  O C A R I N A   O F   T I M E  ~
"""

FOOT_ASCII = r"""
                    *  .  *    .  *  .
                   (c) 1998  Nintendo
"""


def render(color: bool | None = None, unicode: bool | None = None) -> str:
    if color is None:
        color = _use_color()
    if unicode is None:
        unicode = _use_unicode()
    g, g2, gb, c, d, r = (GOLD, GOLD2, GOLD_BRIGHT, CYAN, DIM, RESET) if color else ("", "", "", "", "", "")
    tri = TRIFORCE_UNI if unicode else TRIFORCE_ASCII
    word = ZELDA_UNI if unicode else ZELDA_ASCII
    sub = SUB_UNI if unicode else SUB_ASCII
    foot = FOOT_UNI if unicode else FOOT_ASCII
    lines = []
    lines.append("")
    for raw in tri.strip("\n").splitlines():
        lines.append(f"{gb}{raw}{r}")
    for raw in word.strip("\n").splitlines():
        if "T H E" in raw:
            lines.append(f"{g2}{raw}{r}")
        else:
            lines.append(f"{g}{raw}{r}")
    for raw in sub.strip("\n").splitlines():
        lines.append(f"{c}{raw}{r}")
    for raw in foot.strip("\n").splitlines():
        if "*" in raw:
            lines.append(f"{c}{raw}{r}")
        else:
            lines.append(f"{d}{raw}{r}")
    rule = "        \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500" if unicode else "        ---------------------------------------------"
    lines.append(f"{d}{rule}{r}")
    lines.append(f"{g2}              FndZlda{r}{d}  \u00b7  Switch 2 Zelda 40th hunter{r}")
    lines.append("")
    return "\n".join(lines) + "\n"


def print_logo() -> None:
    enable_windows_ansi()
    sys.stdout.write(render())
    sys.stdout.flush()
