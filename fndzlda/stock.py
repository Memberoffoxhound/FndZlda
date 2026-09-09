"""Stock classification from retailer HTML/JSON.

A listing is IN_STOCK only when:
  1. the page title is the Zelda 40th Switch 2 SKU we asked for
  2. a buy/pre-order signal is present
  3. no sold-out / coming-soon signal wins
  4. price is at or under the cap (skip marketplace scalpers)
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass

from fndzlda.catalog import MSRP, PRICE_CAP, PRICE_FLOOR, Listing
from fndzlda.identity import extract_price, matches_item, page_title, strip_tags

SOLD_OUT = [
    r"sold[\s-]*out",
    r"out[\s-]*of[\s-]*stock",
    r"currently unavailable",
    r"coming soon",
    r"not yet available",
    r"preorders? have sold out",
    r"we['\u2019]?re out of stock",
    r"this item is (currently )?unavailable",
    r"unavailable for purchase",
    r"check back on release",
    r"notify[\s-]*me when",
    r'"buttonstate"\s*:\s*"sold_out"',
    r'"availabilitystatus"\s*:\s*"out_of_stock"',
    r'"purchasable"\s*:\s*false',
    r'"instock"\s*:\s*false',
    r'"availability"\s*:\s*"outofstock"',
]

IN_STOCK = [
    r"add to cart",
    r"add to bag",
    r"pre-?order now",
    r"preorder",
    r"\bbuy now\b",
    r"pick up (here|today)",
    r'"buttonstate"\s*:\s*"add_to_cart"',
    r'"availabilitystatus"\s*:\s*"in_stock"',
    r'"purchasable"\s*:\s*true',
    r'"instock"\s*:\s*true',
    r'"availability"\s*:\s*"instock"',
    r"ships (today|tomorrow|in )",
]

PREORDER_OK = [
    r"pre-?order now",
    r'"buttonstate"\s*:\s*"pre_order"',
    r"preorder now",
]


@dataclass
class StockResult:
    listing: Listing
    in_stock: bool
    status: str
    title: str
    price: float | None
    url: str
    reason: str
    asin: str = ""


def _count(patterns: list[str], blob: str) -> int:
    n = 0
    for pat in patterns:
        if re.search(pat, blob, re.I):
            n += 1
    return n


def classify_blob(blob: str) -> tuple[bool, str, str]:
    sold = _count(SOLD_OUT, blob)
    buy = _count(IN_STOCK, blob)
    pre = _count(PREORDER_OK, blob)
    if sold and sold >= buy:
        return False, "SOLD_OUT", f"sold-out signals={sold} buy={buy}"
    if buy or pre:
        return True, "IN_STOCK", f"buy signals={buy} preorder={pre} sold-out={sold}"
    return False, "UNKNOWN", f"no buy signal (sold-out={sold})"


def amazon_asins(html: str) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for m in re.finditer(
        r'data-asin="([A-Z0-9]{10})"[^>]*>[\s\S]{0,2500}?alt="([^"]+)"',
        html or "",
        re.I,
    ):
        rows.append((m.group(1), m.group(2)))
    if rows:
        return rows
    for m in re.finditer(r'data-asin="([A-Z0-9]{10})"', html or ""):
        rows.append((m.group(1), ""))
    return rows


def pick_amazon_asin(html: str, item: str) -> tuple[str, str]:
    for asin, title in amazon_asins(html):
        if title and matches_item(title, item):  # type: ignore[arg-type]
            return asin, title
    for asin, title in amazon_asins(html):
        blob = (title or "").lower()
        if "zelda" in blob and "40" in blob:
            if item == "controller" and "controller" in blob:
                return asin, title
            if item == "console" and "controller" not in blob and "case" not in blob:
                return asin, title
    return "", ""


def from_page(listing: Listing, html: str, url: str, asin: str = "") -> StockResult:
    title = page_title(html)
    if not title:
        title = strip_tags((html or "")[:800])
    if html and not matches_item(title, listing.item) and listing.retailer != "amazon":
        window = (html or "")[:80_000]
        if not (listing.sku and listing.sku in window and re.search(r"zelda", window, re.I)):
            return StockResult(
                listing, False, "WRONG_ITEM", title, None, url, "title did not match Zelda 40th SKU"
            )
    price = extract_price(html or "", hint=MSRP[listing.item])
    cap = PRICE_CAP[listing.item]
    floor = PRICE_FLOOR[listing.item]
    blob = (html or "").lower()
    in_stock, status, reason = classify_blob(blob)
    if in_stock and price is not None and price > cap:
        return StockResult(
            listing,
            False,
            "SCALPER",
            title,
            price,
            url,
            f"price ${price:.2f} over cap ${cap:.2f}",
            asin=asin,
        )
    if in_stock and price is not None and price < floor:
        return StockResult(
            listing,
            False,
            "WRONG_PRICE",
            title,
            price,
            url,
            f"price ${price:.2f} below floor ${floor:.2f} (plan/accessory, not the SKU)",
            asin=asin,
        )
    return StockResult(listing, in_stock, status, title, price, url, reason, asin=asin)


def parse_json_ld(html: str) -> dict:
    for m in re.finditer(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html or "",
        re.I | re.S,
    ):
        raw = m.group(1).strip()
        try:
            data = json.loads(raw)
        except Exception:
            continue
        if isinstance(data, list) and data:
            data = data[0]
        if isinstance(data, dict):
            return data
    return {}
