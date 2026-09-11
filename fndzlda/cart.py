"""Open the default browser to add-to-cart / pre-order, then checkout.

Best Buy's yellow Pre-Order button is the skuId add-to-cart URL.
We hammer that URL N times in a row so a drop queue / cart has more
than one chance to catch. We cannot press the DOM button inside Chrome;
this is the same navigation that button performs.
"""
from __future__ import annotations

import time
import webbrowser

from fndzlda.catalog import Listing
from fndzlda.stock import StockResult

_opened_carts: set[str] = set()


def reset_opened_carts() -> None:
    _opened_carts.clear()


def should_open_browser(key: str, opened: set[str], again: bool = False) -> bool:
    return bool(again) or key not in opened


def add_to_cart_url(listing: Listing, asin: str = "") -> str:
    r = listing.retailer
    sku = listing.sku
    extra = listing.extra
    if r == "bestbuy":
        sid = extra.get("sku_id", sku)
        return f"https://www.bestbuy.com/cart/r/add-to-cart?skuId={sid}"
    if r == "walmart":
        iid = extra.get("item_id", sku)
        return f"https://www.walmart.com/cart?action=add&items={iid}"
    if r == "target":
        tcin = extra.get("tcin", sku)
        return f"https://www.target.com/co-addtocart?tcin={tcin}&quantity=1"
    if r == "gamestop":
        pid = extra.get("pid", sku)
        return (
            "https://www.gamestop.com/on/demandware.store/Sites-gamestop-us-Site/"
            f"default/Cart-AddProduct?pid={pid}&quantity=1"
        )
    if r == "amazon":
        code = asin or sku
        if re_asin(code):
            return f"https://www.amazon.com/gp/aws/cart/add.html?ASIN.1={code}&Quantity.1=1"
        return listing.url
    if r == "nintendo":
        return listing.url
    return listing.url


def checkout_url(listing: Listing, asin: str = "") -> str:
    r = listing.retailer
    if r == "bestbuy":
        return listing.url
    if r == "walmart":
        return "https://www.walmart.com/checkout/"
    if r == "target":
        return "https://www.target.com/co-review"
    if r == "gamestop":
        return "https://www.gamestop.com/checkout"
    if r == "amazon":
        return "https://www.amazon.com/gp/cart/view.html?ref_=nav_cart"
    if r == "nintendo":
        return "https://www.nintendo.com/us/store/cart"
    return listing.url


def re_asin(code: str) -> bool:
    import re

    return bool(re.fullmatch(r"[A-Z0-9]{10}", code or ""))


def fire_browser(
    hit: StockResult,
    delay_s: float = 2.2,
    dry_run: bool = False,
    again: bool = False,
    tries: int = 1,
) -> list[str]:
    """Open add-to-cart / pre-order. Best Buy repeats the button URL `tries` times."""
    cart = add_to_cart_url(hit.listing, hit.asin)
    check = checkout_url(hit.listing, hit.asin)
    burst = max(1, int(tries))
    if hit.listing.retailer == "bestbuy":
        planned = [cart] * burst
        if check and check != cart:
            planned.append(check)
    else:
        planned = [cart] if check == cart else [cart, check]
    if dry_run:
        return planned
    if cart in _opened_carts and not again:
        return []
    _opened_carts.add(cart)
    if hit.listing.retailer == "bestbuy":
        gap = 0.35
        for i in range(burst):
            webbrowser.open(cart, new=2)
            if i + 1 < burst:
                time.sleep(gap)
        if check != cart:
            time.sleep(max(0.4, min(delay_s, 1.2)))
            webbrowser.open(check, new=2)
        return planned
    webbrowser.open(cart, new=2)
    if check != cart:
        time.sleep(max(0.4, delay_s))
        webbrowser.open(check, new=2)
    return planned
