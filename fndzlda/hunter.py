"""Scan every listing for the chosen items."""
from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote

from fndzlda.catalog import Listing, listings_for
from fndzlda.httputil import fetch
from fndzlda.identity import matches_item
from fndzlda.stock import StockResult, from_page, pick_amazon_asin


def _check_one(listing: Listing, getter=fetch) -> StockResult:
    page = getter(listing.url)
    if page.status == 0 and not page.body:
        return StockResult(
            listing, False, "ERROR", "", None, listing.url, page.error or "fetch failed"
        )
    if listing.retailer == "amazon" and listing.extra.get("search"):
        asin, title = pick_amazon_asin(page.body, listing.item)
        if not asin:
            q = listing.extra.get("query")
            if q:
                search_url = f"https://www.amazon.com/s?k={quote(q)}"
                page = getter(search_url)
                asin, title = pick_amazon_asin(page.body, listing.item)
        if not asin:
            return StockResult(
                listing,
                False,
                "UNKNOWN",
                title,
                None,
                listing.url,
                "no Amazon result matching Zelda 40th SKU",
            )
        product_url = f"https://www.amazon.com/dp/{asin}"
        prod = getter(product_url)
        hit = from_page(listing, prod.body, prod.url or product_url, asin=asin, status=prod.status)
        if not hit.title:
            hit.title = title
        return hit
    return from_page(listing, page.body, page.url or listing.url, status=page.status)


def scan(
    want: set[str],
    workers: int = 6,
    getter=fetch,
    shops: set[str] | None = None,
) -> list[StockResult]:
    rows = listings_for(want, shops)
    out: list[StockResult] = []
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        futs = {pool.submit(_check_one, listing, getter): listing for listing in rows}
        for fut in as_completed(futs):
            try:
                out.append(fut.result())
            except Exception as e:
                listing = futs[fut]
                out.append(
                    StockResult(listing, False, "ERROR", "", None, listing.url, str(e))
                )
    out.sort(key=lambda r: (r.listing.item, r.listing.retailer))
    return out


def is_actionable(hit: StockResult) -> bool:
    if not hit.in_stock:
        return False
    if hit.status in ("WRONG_ITEM", "SCALPER", "ERROR", "WRONG_PRICE", "COMING_SOON"):
        return False
    if hit.price is None:
        return False
    if hit.title and not matches_item(hit.title, hit.listing.item):
        if hit.listing.retailer != "amazon":
            return False
    return True


def next_wait(hit_count: int, interval: float, hit_pause: float = 120.0) -> float:
    """Seconds until the next full scan. Hits do not pause other shops."""
    _ = hit_count, hit_pause
    return max(3.0, interval)


def shop_cooldown_left(retailer: str, until: dict[str, float], now: float | None = None) -> float:
    """Seconds left on this store's auto-add cooldown, or 0."""
    t = time.monotonic() if now is None else now
    left = float(until.get(retailer, 0.0)) - t
    return left if left > 0 else 0.0


def mark_shop_cooldown(
    retailer: str,
    until: dict[str, float],
    pause: float,
    now: float | None = None,
) -> float:
    t = time.monotonic() if now is None else now
    until[retailer] = t + max(0.0, pause)
    return until[retailer]
