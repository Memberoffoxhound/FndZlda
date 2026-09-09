"""Official US listings for the Zelda 40th Anniversary Switch 2 hardware.

SKUs collected September 2026 from Nintendo, Best Buy, Target, Walmart,
and GameStop. Amazon is searched by UPC because the ASIN was not stable
at listing time.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Literal

ItemId = Literal["console", "controller"]

CONSOLE = "console"
CONTROLLER = "controller"

MSRP = {
    CONSOLE: 519.99,
    CONTROLLER: 99.99,
}

# Reject marketplace scalper prices a bit above MSRP, keep a small buffer.
PRICE_CAP = {
    CONSOLE: 560.0,
    CONTROLLER: 130.0,
}
# Protection plans / cases parse as cheap "$35" — ignore those as the SKU price.
PRICE_FLOOR = {
    CONSOLE: 450.0,
    CONTROLLER: 70.0,
}


@dataclass(frozen=True)
class Listing:
    retailer: str
    item: ItemId
    sku: str
    url: str
    upc: str = ""
    extra: dict = field(default_factory=dict)


CONSOLE_UPC = "045496885434"
CONTROLLER_UPC = "045496886325"

LISTINGS: list[Listing] = [
    Listing(
        "nintendo",
        CONSOLE,
        "121642",
        "https://www.nintendo.com/us/store/products/nintendo-switch-2-the-legend-of-zelda-40th-anniversary-edition-121642/",
        CONSOLE_UPC,
    ),
    Listing(
        "nintendo",
        CONTROLLER,
        "127074",
        "https://www.nintendo.com/us/store/products/nintendo-switch-2-pro-controller-the-legend-of-zelda-40th-anniversary-edition-127074/",
        CONTROLLER_UPC,
    ),
    Listing(
        "bestbuy",
        CONSOLE,
        "6691841",
        "https://www.bestbuy.com/product/switch-2-the-legend-of-zelda-40th-anniversary-edition/J7GSL57HTY/sku/6691841",
        CONSOLE_UPC,
        {"sku_id": "6691841"},
    ),
    Listing(
        "bestbuy",
        CONTROLLER,
        "6691849",
        "https://www.bestbuy.com/product/nintendo-switch-2-pro-controller-the-legend-of-zelda-40th-anniversary-edition-multi/J7GSL57W27/sku/6691849",
        CONTROLLER_UPC,
        {"sku_id": "6691849"},
    ),
    Listing(
        "target",
        CONSOLE,
        "1013322047",
        "https://www.target.com/p/nintendo-switch-2-the-legend-of-zelda-40th-anniversary-edition-console-system/-/A-1013322047",
        CONSOLE_UPC,
        {"tcin": "1013322047"},
    ),
    Listing(
        "target",
        CONTROLLER,
        "1013213521",
        "https://www.target.com/p/nintendo-switch-2-pro-controller-the-legend-of-zelda-40th-anniversary-edition/-/A-1013213521",
        CONTROLLER_UPC,
        {"tcin": "1013213521"},
    ),
    Listing(
        "walmart",
        CONSOLE,
        "21002656445",
        "https://www.walmart.com/ip/Nintendo-Switch-2-The-Legend-of-Zelda-40th-Anniversary-Edition/21002656445",
        CONSOLE_UPC,
        {"item_id": "21002656445"},
    ),
    Listing(
        "walmart",
        CONTROLLER,
        "20954470204",
        "https://www.walmart.com/ip/Nintendo-Switch-2-Pro-Controller-The-Legend-of-Zelda-40th-Anniversary-Edition/20954470204",
        CONTROLLER_UPC,
        {"item_id": "20954470204"},
    ),
    Listing(
        "gamestop",
        CONSOLE,
        "20037854",
        "https://www.gamestop.com/consoles-hardware/nintendo-switch-2/products/nintendo-switch-2-the-legend-of-zelda-40th-anniversary-edition/20037854.html",
        CONSOLE_UPC,
        {"pid": "20037854"},
    ),
    Listing(
        "gamestop",
        CONTROLLER,
        "20037855",
        "https://www.gamestop.com/gaming-accessories/controllers/nintendo-switch-2/products/nintendo-switch-2-pro-controller-the-legend-of-zelda---40th-anniversary-edition/20037855.html",
        CONTROLLER_UPC,
        {"pid": "20037855"},
    ),
    Listing(
        "amazon",
        CONSOLE,
        CONSOLE_UPC,
        f"https://www.amazon.com/s?k={CONSOLE_UPC}&i=videogames",
        CONSOLE_UPC,
        {
            "search": True,
            "query": "Nintendo Switch 2 The Legend of Zelda 40th Anniversary Edition console",
        },
    ),
    Listing(
        "amazon",
        CONTROLLER,
        CONTROLLER_UPC,
        f"https://www.amazon.com/s?k={CONTROLLER_UPC}&i=videogames",
        CONTROLLER_UPC,
        {
            "search": True,
            "query": "Nintendo Switch 2 Pro Controller The Legend of Zelda 40th Anniversary",
        },
    ),
]

ITEM_LABEL = {
    CONSOLE: "Switch 2 Zelda 40th console",
    CONTROLLER: "Zelda 40th Pro Controller",
}

RETAILER_LABEL = {
    "nintendo": "Nintendo",
    "bestbuy": "Best Buy",
    "target": "Target",
    "walmart": "Walmart",
    "gamestop": "GameStop",
    "amazon": "Amazon",
}


SHOP_IDS = ("nintendo", "bestbuy", "target", "walmart", "gamestop", "amazon")

# Plain names people type, including the usual misspellings.
_SHOP_ALIASES: dict[str, tuple[str, ...]] = {
    "nintendo": ("nintendo", "nintend", "nintindo", "ninten", "nin", "eshop"),
    "bestbuy": ("bestbuy", "best buy", "best-buy", "bestby", "bestbey", "bb", "bby"),
    "target": ("target", "targt", "tarjet", "trget", "tgt"),
    "walmart": ("walmart", "wal-mart", "wal mart", "wally", "walmarts", "wmt"),
    "gamestop": ("gamestop", "game stop", "game-stop", "gamestp", "gamestp", "gstop", "gs"),
    "amazon": ("amazon", "amazn", "amazom", "amazoon", "amzn"),
}

_ALL_SHOP_WORDS = {"all", "every", "everything", "any", "anyone", "allstores", "*"}


def _norm_shop_token(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (s or "").lower())


def _score_shop(token: str, shop: str) -> float:
    needle = _norm_shop_token(token)
    if not needle:
        return 0.0
    best = 0.0
    for alias in _SHOP_ALIASES[shop]:
        alias_n = _norm_shop_token(alias)
        if needle == alias_n:
            return 1.0
        if needle in alias_n or alias_n in needle:
            best = max(best, 0.92)
        best = max(best, SequenceMatcher(None, needle, alias_n).ratio())
    return best


def match_shop(token: str) -> str | None:
    """Map one typed store name to a shop id. Typos are ok."""
    raw = (token or "").strip().lower()
    if not raw or raw in ("and", "or", "the", "store", "stores"):
        return None
    best_shop = ""
    best_score = 0.0
    for shop in SHOP_IDS:
        score = _score_shop(raw, shop)
        if score > best_score:
            best_score = score
            best_shop = shop
    # Short codes like bb/gs need an exact alias hit; longer names can be fuzzy.
    need = 0.78 if len(_norm_shop_token(raw)) >= 5 else 0.99
    if best_score >= need:
        return best_shop
    return None


def parse_shops(text: str) -> tuple[set[str], list[str]]:
    """Parse a comma-separated store list. Returns (shops, unknown tokens)."""
    raw = (text or "").strip().lower()
    if not raw:
        return set(), []
    compact = _norm_shop_token(raw)
    if raw in _ALL_SHOP_WORDS or compact in _ALL_SHOP_WORDS:
        return set(SHOP_IDS), []
    chunks = [c.strip() for c in re.split(r"[,/;]+", text) if c.strip()]
    shops: set[str] = set()
    unknown: list[str] = []

    def eat(token: str) -> None:
        hit = match_shop(token)
        if hit:
            shops.add(hit)
        else:
            unknown.append(token.strip())

    for chunk in chunks:
        if match_shop(chunk):
            eat(chunk)
            continue
        bits = [b for b in re.split(r"\s+", chunk) if b and b.lower() not in ("and", "or", "&")]
        if len(bits) > 1:
            for bit in bits:
                eat(bit)
        else:
            eat(chunk)
    return shops, unknown


def listings_for(want: set[str], shops: set[str] | None = None) -> list[Listing]:
    rows = [row for row in LISTINGS if row.item in want]
    if shops:
        rows = [row for row in rows if row.retailer in shops]
    return rows
