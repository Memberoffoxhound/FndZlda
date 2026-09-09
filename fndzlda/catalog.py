"""Official US listings for the Zelda 40th Anniversary Switch 2 hardware.

SKUs collected September 2026 from Nintendo, Best Buy, Target, Walmart,
and GameStop. Amazon is searched by UPC because the ASIN was not stable
at listing time.
"""
from __future__ import annotations

from dataclasses import dataclass, field
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
        {"search": True},
    ),
    Listing(
        "amazon",
        CONTROLLER,
        CONTROLLER_UPC,
        f"https://www.amazon.com/s?k={CONTROLLER_UPC}&i=videogames",
        CONTROLLER_UPC,
        {"search": True},
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


def listings_for(want: set[str]) -> list[Listing]:
    return [row for row in LISTINGS if row.item in want]
