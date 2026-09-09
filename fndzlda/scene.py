"""NES cave old man, Master Sword, Navi, and miss quotes."""
from __future__ import annotations

import os
import sys

GOLD = "\033[38;5;220m"
GOLD_BRIGHT = "\033[1;38;5;227m"
CYAN = "\033[1;38;5;87m"
RED = "\033[38;5;174m"
DIM = "\033[38;5;94m"
RESET = "\033[0m"

CAVE = r"""
        ################################
        #                              #
        #           .----.             #
        #          / o  o \            #
        #          |  ..  |            #
        #          | '--' |            #
        #         _|______|_           #
        #        /  ######  \          #
        #       |  /||||||\  |         #
        #       | |  |  |  | |         #
        #        \_|______|_/          #
        #          |  /\  |            #
        #         /_|    |_\           #
        #                              #
        #  IT'S DANGEROUS TO GO ALONE! #
        #         TAKE THIS!           #
        ################################
"""

SWORD = r"""
                    /\
                   /  \
                   \  /
                   |  |
                   |/\ |
                  /|  |\
                 | |  | |
               __| |  | |__
              /    |  |    \
              \____|  |____/
                   |  |
                   |  |
                   |  |
                   |  |
                  _|  |_
                 |______|
                   |  |
                   |  |
                  /    \
               MASTER SWORD
"""

NAVI = r"""
           *  .  *
          (  o o  )      HEY! LISTEN!!!
           \  -  /
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


def _use_color() -> bool:
    if os.environ.get("NO_COLOR") or os.environ.get("FNDZLDA_PLAIN"):
        return False
    try:
        return sys.stdout.isatty()
    except Exception:
        return False


def _paint_block(block: str, color: str, reset: str) -> str:
    lines = []
    for raw in block.strip("\n").splitlines():
        lines.append(f"{color}{raw}{reset}")
    return "\n".join(lines)


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
