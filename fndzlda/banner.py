"""Ocarina of Time title art for the terminal.

Hylian Shield splash — letters and symbols only.
"""
from __future__ import annotations

import base64
import os
import ssl
import sys
import urllib.request
import zlib
from pathlib import Path

GOLD = "\033[38;5;220m"
GOLD2 = "\033[38;5;178m"
GOLD_BRIGHT = "\033[1;38;5;227m"
CYAN = "\033[1;38;5;87m"
RED = "\033[38;5;174m"
RED_BRIGHT = "\033[1;38;5;196m"
DIM = "\033[38;5;94m"
RESET = "\033[0m"

_DIR = Path(__file__).resolve().parent
_LOGO_Z_URL = (
    "https://raw.githubusercontent.com/Memberoffoxhound/FndZlda/main/fndzlda/banner_logo_z.txt"
)


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


def _fetch_logo_z(dest: Path) -> None:
    req = urllib.request.Request(_LOGO_Z_URL, headers={"User-Agent": "FndZlda"})
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=12, context=ctx) as resp:
        dest.write_bytes(resp.read())


def _load_logo() -> str:
    raw = _DIR / "banner_art.txt"
    try:
        if raw.is_file():
            text = raw.read_text(encoding="utf-8")
            if text.lstrip().startswith("@"):
                return text
    except OSError:
        pass
    zpath = _DIR / "banner_logo_z.txt"
    try:
        if not zpath.is_file() or zpath.stat().st_size < 100:
            _fetch_logo_z(zpath)
        blob = zpath.read_text(encoding="ascii").encode("ascii")
        return zlib.decompress(base64.b64decode(blob)).decode("utf-8")
    except Exception:
        return ""


LOGO = _load_logo()


def _paint_block(block: str, color: str, reset: str) -> str:
    lines = []
    for raw in block.strip("\n").splitlines():
        lines.append(f"{color}{raw}{reset}")
    return "\n".join(lines)


def render(color: bool | None = None, unicode: bool | None = None) -> str:
    if color is None:
        color = _use_color()
    g, g2, gb, d, r = (
        (GOLD, GOLD2, GOLD_BRIGHT, DIM, RESET) if color else ("", "", "", "", "")
    )
    parts = [""]
    if LOGO.strip():
        parts.append(_paint_block(LOGO, g, r))
    parts.extend(
        [
            f"{gb}                 O C A R I N A   O F   T I M E{r}",
            f"{d}        ---------------------------------------------{r}",
            f"{g2}              FndZlda{r}{d}  ·  Switch 2 Zelda 40th hunter{r}",
            "",
        ]
    )
    return "\n".join(parts) + "\n"


def render_ocarina(color: bool | None = None) -> str:
    if color is None:
        color = _use_color()
    gb, r = (GOLD_BRIGHT, RESET) if color else ("", "")
    return f"{gb}                     O C A R I N A  O F  T I M E{r}\n"


CAVE = r"""
        ################################
        #                              #
        #           .----.             #
        #          / o  o \\            #
        #          |  ..  |            #
        #          | '--' |            #
        #         _|______|_           #
        #        /  ######  \\          #
        #       |  /||||||\\  |         #
        #       | |  |  |  | |         #
        #        \\_|______|_/          #
        #          |  /\\  |            #
        #         /_|    |_\\           #
        #                              #
        #  IT'S DANGEROUS TO GO ALONE! #
        #         TAKE THIS!           #
        ################################
"""

SWORD = r"""
                    /\\
                   /  \\
                   \\  /
                   |  |
                   |/\\ |
                  /|  |\\
                 | |  | |
               __| |  | |__
              /    |  |    \\
              \\____|  |____/
                   |  |
                   |  |
                   |  |
                   |  |
                  _|  |_
                 |______|
                   |  |
                   |  |
                  /    \\
               MASTER SWORD
"""

NAVI = r"""
           *  .  *
          (  o o  )      HEY! LISTEN!!!
           \\  -  /
            *   *
"""

MISS_QUOTES = (
    ("You've met with a terrible fate, haven't you?", "Majora's Mask"),
    ("Sorry, I can't give credit. Come back when you're a little... mmm... richer!", "Hyrule shopkeeper"),
    ("The treasure chest is empty...", "A Link to the Past"),
    ("You don't have enough Rupees.", "Every shop in Hyrule"),
    ("This door is locked.", "every dungeon"),
    ("I am still not ready...", "Princess Zelda"),
    ("Keep your sword equipped. You never know when you might run into trouble. ...Not this pass.", "Kaepora Gaebora"),
    ("Your hearts are empty.", "Game Over"),
    ("Nothing happened.", "using an item in the wrong place"),
    ("The Master Sword sleeps still.", "the Pedestal of Time"),
)


def render_intro(color: bool | None = None) -> str:
    if color is None:
        color = _use_color()
    g, gb, d, r = (GOLD, GOLD_BRIGHT, DIM, RESET) if color else ("", "", "", "")
    cave = _paint_block(CAVE, g, r)
    sword = _paint_block(SWORD, gb, r)
    return f"\n{cave}\n\n{sword}\n{d}              FndZlda  ·  US Zelda 40th hunter{r}\n\n"


def disappointment(scan_n: int, color: bool | None = None) -> str:
    if color is None:
        color = _use_color()
    q, src = MISS_QUOTES[(max(1, scan_n) - 1) % len(MISS_QUOTES)]
    c, d, rst = (RED, DIM, RESET) if color else ("", "", "")
    return f'  {c}"{q}"{rst}\n  {d}    — {src}{rst}'


def hey_listen(color: bool | None = None) -> str:
    if color is None:
        color = _use_color()
    c, rst = (CYAN, RESET) if color else ("", "")
    return _paint_block(NAVI, c, rst) + "\n"


def print_logo() -> None:
    enable_windows_ansi()
    sys.stdout.write(render())
    sys.stdout.flush()
