"""Open the default browser to add-to-cart, then checkout.

Retailers do not all expose a public GET add-to-cart. We use the official
deep links that do exist, then the checkout URL. The shopper still has to
be logged in for Nintendo / some carts — the browser is theirs.

Best Buy's click-cart URL adds one unit on every visit. The two-minute
rescan must not open it again or the cart stacks quantity.
"""
from __future__ import annotations

import time
import webbrowser

from fndzlda.catalog import Listing
from fndzlda.stock import StockResult

# Add-to-cart URLs already opened this process. GET add-to-cart is not idempotent.
_opened_carts: set[str] = set()


def reset_opened_carts() -> None:
    _opened_carts.clear()


def should_open_browser(key: str, opened: set[str], again: bool = False) -> bool:
    """False if this listing was already added to the cart this hunt."""
    return bool(again) or key not in opened


def add_to_cart_url(listing: Listing, asin: str = "") -> str:
    r = listing.retailer
    sku = listing.sku
    extra = listing.extra
    if r == "bestbuy":
        # api.bestbuy.com/click/.../cart is a JS stub that often fails in Discord /
        # in-app browsers. The site add-to-cart path lands on the real cart.
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
        # fast-track 404s / bounces for empty carts; cart is the reliable next step
        return "https://www.bestbuy.com/cart"
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
) -> list[str]:
    """Open add-to-cart, then checkout, in the user's default browser.

    The add-to-cart link is opened at most once per URL this process unless
    again=True. Best Buy / Walmart / Target / GameStop all add a unit on GET.
    """
    cart = add_to_cart_url(hit.listing, hit.asin)
    check = checkout_url(hit.listing, hit.asin)
    planned = [cart] if check == cart else [cart, check]
    if dry_run:
        return planned
    if cart in _opened_carts and not again:
        return []
    _opened_carts.add(cart)
    webbrowser.open(cart, new=2)
    time.sleep(max(0.4, delay_s))
    if check != cart:
        webbrowser.open(check, new=2)
    return planned
