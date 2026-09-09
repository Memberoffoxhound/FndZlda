"""Make sure a page is the Zelda 40th Switch 2 SKU — not PowerA, OLED, or a case."""
from __future__ import annotations

import html as htmlmod
import re

from fndzlda.catalog import CONSOLE, CONTROLLER, ItemId

_TAG = re.compile(r"<[^>]+>", re.S)
_WS = re.compile(r"\s+")
_TITLE = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)
_OG = re.compile(
    r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\'](.*?)["\']',
    re.I | re.S,
)
_OG2 = re.compile(
    r'<meta[^>]+content=["\'](.*?)["\'][^>]+property=["\']og:title["\']',
    re.I | re.S,
)
_H1 = re.compile(r"<h1[^>]*>(.*?)</h1>", re.I | re.S)

CONSOLE_FORBID = (
    "pro controller",
    "carrying case",
    "screen protector",
    "powera",
    "amiibo",
    "wired controller",
    "enhanced wireless",
)
CONTROLLER_FORBID = (
    "carrying case",
    "screen protector",
    "powera",
    "amiibo",
    "console system",
    "oled",
)


def strip_tags(blob: str) -> str:
    text = htmlmod.unescape(_TAG.sub(" ", blob or ""))
    return _WS.sub(" ", text).strip()


def page_title(html: str) -> str:
    for pat in (_TITLE, _OG, _OG2, _H1):
        m = pat.search(html or "")
        if m:
            t = strip_tags(m.group(1))
            if t and t.lower() not in ("best buy", "amazon.com", "target", "walmart"):
                return t
    return ""


def _norm(s: str) -> str:
    return (
        (s or "")
        .lower()
        .replace("\u2122", " ")
        .replace("\u00ae", " ")
        .replace("\u2013", " ")
        .replace("\u2014", " ")
    )


def _has_switch2(t: str) -> bool:
    return "switch 2" in t or "switch2" in t or "switch  2" in t


def _has_zelda_40(t: str) -> bool:
    if "zelda" not in t:
        return False
    return "40th" in t or "anniversary" in t


def matches_item(title: str, item: ItemId) -> bool:
    t = _norm(title)
    if not t or not _has_zelda_40(t):
        return False
    if not _has_switch2(t):
        return False
    if item == CONSOLE:
        if any(x in t for x in CONSOLE_FORBID):
            return False
        return True
    if item == CONTROLLER:
        if any(x in t for x in CONTROLLER_FORBID):
            return False
        return "pro controller" in t or "pro-controller" in t
    return False


def extract_price(text: str, hint: float | None = None) -> float | None:
    """Best-effort product price. Prefers amounts near `hint` (MSRP)."""
    found: list[float] = []
    for m in re.finditer(r"\$\s*([0-9]{2,4}(?:\.[0-9]{2})?)", text or ""):
        try:
            val = float(m.group(1))
        except ValueError:
            continue
        if 15 <= val <= 900:
            found.append(val)
    if not found:
        return None
    if hint:
        near = [v for v in found if abs(v - hint) <= 50]
        if near:
            return min(near, key=lambda v: abs(v - hint))
    for prefer in (519.99, 99.99, 89.99, 519.0, 99.0):
        for v in found:
            if abs(v - prefer) < 0.02:
                return v
    return found[0]
