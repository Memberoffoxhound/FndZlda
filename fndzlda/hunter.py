"""Scan every listing for the chosen items."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed

from fndzlda.catalog import Listing, listings_for
from fndzlda.httputil import fetch
from fndzlda.identity import matches_item
from fndzlda.stock import StockResult, from_page, pick_amazon_asin


def _check_one(listing: Listing, getter=fetch) -> StockResult:
    page = getter(listing.url)
    if page.status == 0:
        return StockResult(
            listing, False, "ERROR", "", None, listing.url, page.error or "fetch failed"
        )
    if listing.retailer == "amazon" and listing.extra.get("search"):
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
        hit = from_page(listing, prod.body, prod.url or product_url, asin=asin)
        if not hit.title:
            hit.title = title
        return hit
    return from_page(listing, page.body, page.url or listing.url)


def scan(want: set[str], workers: int = 6, getter=fetch) -> list[StockResult]:
    rows = listings_for(want)
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
    if hit.status in ("WRONG_ITEM", "SCALPER", "ERROR"):
        return False
    if hit.title and not matches_item(hit.title, hit.listing.item):
        if hit.listing.retailer != "amazon":
            return False
    return True
