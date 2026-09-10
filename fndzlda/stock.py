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
    r"(?<![a-z])sold[\s-]*out(?![a-z])",
    r"out[\s-]*of[\s-]*stock",
    r"currently unavailable",
    r"(?<![a-z])coming soon(?![a-z])",
    r"not yet available",
    r"preorders? have sold out",
    r"we['’]?re out of stock",
    r"this item is (currently )?unavailable",
    r"unavailable for purchase",
    r"check back on release",
    r"notify[\s-]*me when",
    r'"buttonstate"\s*:\s*"sold_out"',
    r'"availabilitystatus"\s*:\s*"out_of_stock"',
    r'"purchasable"\s*:\s*false',
    r'"instock"\s*:\s*false',
    r'"availability"\s*:\s*"outofstock"',
    r"schema\.org/outofstock",
    r"disabled-add-to-cart",
    r"<[^>]*\bdisabled\b[^>]*>\s*add to (?:cart|bag)",
]

IN_STOCK = [
    r"add to cart",
    r"add to bag",
    r"pre-?order now",
    r"(?<![a-z])preorder now(?![a-z])",
    r"\bbuy now\b",
    r"pick up (here|today)",
    r'"buttonstate"\s*:\s*"add_to_cart"',
    r'"availabilitystatus"\s*:\s*"in_stock"',
    r'"purchasable"\s*:\s*true',
    r'"instock"\s*:\s*true',
    r'"availability"\s*:\s*"instock"',
    r"schema\.org/instock",
    r"ships (today|tomorrow|in )",
]

# Preorder pages that are still live (button is Preorder, not sold out).
PREORDER_OK = [
    r"pre-?order now",
    r'"buttonstate"\s*:\s*"pre_order"',
    r"preorder now",
]

_WALL = (
    "attention required",
    "cloudflare",
    "to discuss automated access",
    "sorry! something went wrong",
    "are you a human",
    "robot or human",
    "captcha",
    "/px/",
    "blockscript",
    '"redirecturl":"/blocked',
)


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


# Target (and others) SSR a disabled Add to cart while sold out. Do not treat that as a buy.
_DISABLED_BUY = re.compile(
    r"<[^>]{0,400}\bdisabled\b[^>]{0,80}>\s*add to (?:cart|bag)\s*</(?:button|span|div|a)>",
    re.I,
)


def classify_blob(blob: str) -> tuple[bool, str, str]:
    """Return (in_stock, status, reason) from a lowered page blob."""
    blob = _DISABLED_BUY.sub(" disabled-add-to-cart ", blob or "")
    sold = _count(SOLD_OUT, blob)
    buy = _count(IN_STOCK, blob)
    pre = _count(PREORDER_OK, blob)
    if sold and sold >= buy:
        if re.search(r"(?<![a-z])coming soon(?![a-z])", blob, re.I) and not re.search(
            r"(?<![a-z])sold[\s-]*out(?![a-z])|out[\s-]*of[\s-]*stock|schema\.org/outofstock",
            blob,
            re.I,
        ):
            return False, "COMING_SOON", f"coming-soon signals sold={sold} buy={buy}"
        return False, "SOLD_OUT", f"sold-out signals={sold} buy={buy}"
    if buy or pre:
        return True, "IN_STOCK", f"buy signals={buy} preorder={pre} sold-out={sold}"
    return False, "UNKNOWN", f"no buy signal (sold-out={sold})"


def amazon_asins(html: str) -> list[tuple[str, str]]:
    """(asin, title) pairs from a search page, skipping sponsored junk when possible."""
    rows: list[tuple[str, str]] = []
    for m in re.finditer(r'data-asin="([A-Z0-9]{10})"', html or "", re.I):
        asin = m.group(1)
        chunk = (html or "")[m.start() : m.start() + 6000]
        title = ""
        alt = re.search(r'alt="([^"]+)"', chunk)
        if alt:
            title = strip_tags(alt.group(1))
        if not title or len(title) < 8:
            h2 = re.search(r"<h2[^>]*>(.*?)</h2>", chunk, re.I | re.S)
            if h2:
                title = strip_tags(h2.group(1))
        if not title or len(title) < 8:
            aria = re.search(r'aria-label="([^"]+)"', chunk)
            if aria:
                title = strip_tags(aria.group(1))
        rows.append((asin, title))
    return rows


def pick_amazon_asin(html: str, item: str) -> tuple[str, str]:
    for asin, title in amazon_asins(html):
        if title and matches_item(title, item):  # type: ignore[arg-type]
            return asin, title
    for asin, title in amazon_asins(html):
        blob = (title or "").lower()
        if "zelda" in blob and ("40" in blob or "anniversary" in blob):
            if item == "controller" and "controller" in blob:
                return asin, title
            if item == "console" and "controller" not in blob and "case" not in blob:
                return asin, title
    return "", ""


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
        nodes: list = []
        if isinstance(data, dict) and isinstance(data.get("@graph"), list):
            nodes = data["@graph"]
        elif isinstance(data, list):
            nodes = data
        elif isinstance(data, dict):
            nodes = [data]
        for node in nodes:
            if not isinstance(node, dict):
                continue
            types = node.get("@type") or ""
            if isinstance(types, list):
                types = " ".join(str(x) for x in types)
            if "product" in str(types).lower() or node.get("offers"):
                return node
    return {}


def _offer_fields(ld: dict) -> tuple[float | None, str]:
    offers = ld.get("offers") or {}
    if isinstance(offers, list) and offers:
        offers = offers[0]
    if not isinstance(offers, dict):
        return None, ""
    price = None
    raw = offers.get("price") or offers.get("lowPrice")
    try:
        if raw is not None and str(raw) != "":
            price = float(raw)
    except (TypeError, ValueError):
        price = None
    avail = str(offers.get("availability") or "")
    return price, avail


def _nintendo_fields(html: str, sku: str) -> tuple[float | None, object, object]:
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html or "", re.S)
    if not m:
        return None, None, None
    try:
        data = json.loads(m.group(1))
    except Exception:
        return None, None, None
    found: dict = {}

    def walk(obj) -> None:
        if found:
            return
        if isinstance(obj, dict):
            if str(obj.get("sku")) == str(sku) and "availability" in obj:
                prices = obj.get('prices({"personalized":false})') or obj.get("prices") or {}
                price = None
                if isinstance(prices, dict):
                    price = prices.get("finalPrice") or prices.get("regularPrice")
                found["price"] = price
                found["availability"] = obj.get("availability")
                found["salable"] = obj.get("isSalableQty")
                return
            for v in obj.values():
                walk(v)
                if found:
                    return
        elif isinstance(obj, list):
            for v in obj:
                walk(v)
                if found:
                    return

    walk(data)
    return found.get("price"), found.get("availability"), found.get("salable")


def _bestbuy_button(html: str, sku: str = "") -> str:
    """This SKU's PDP buttonState, e.g. COMING_SOON / ADD_TO_CART / SOLD_OUT."""
    blob = html or ""
    if sku:
        m = re.search(
            re.escape(str(sku)) + r'.{0,500}"buttonState"\s*:\s*"([A-Z_]+)"',
            blob,
            re.I | re.S,
        )
        if m:
            return m.group(1).upper()
    m = re.search(
        r'"buttonStates"\s*:\s*\[\s*\{[^}]*"buttonState"\s*:\s*"([A-Z_]+)"',
        blob,
        re.I,
    )
    return m.group(1).upper() if m else ""


def _looks_wall(html: str, status: int) -> bool:
    # 412: Walmart PerimeterX / Akamai-style bot challenges
    if status in (0, 403, 412, 429, 503):
        if not html or len(html) < 8000:
            return True
    blob = (html or "").lower()
    return any(w in blob for w in _WALL) and len(html or "") < 12000




def _amazon_offer(html: str) -> tuple[bool, str, str]:
    """Amazon PDP buyability using real cart controls, not page-wide text.

    Amazon often shows "Pre-order now" / Buy Now chrome when quantity is
    already gone (checkout then says unavailable). Only trust an actual
    add-to-cart or pre-order submit control. Never use the generic
    page-wide "add to cart" / "pre-order now" text counters for Amazon.
    """
    blob = html or ""
    has_atc = bool(
        re.search(r'id=["\']add-to-cart-button["\']', blob, re.I)
        or re.search(r'name=["\']submit\.add-to-cart["\']', blob, re.I)
    )
    has_preorder_submit = bool(
        re.search(r'name=["\']submit\.pre-order["\']', blob, re.I)
        or re.search(r'id=["\']submit\.pre-order["\']', blob, re.I)
    )
    if has_atc or has_preorder_submit:
        kind = "add-to-cart" if has_atc else "pre-order submit"
        return True, "IN_STOCK", f"amazon {kind} present"

    avails: list[str] = []
    for m in re.finditer(r'id=["\']availability["\'][^>]*>(.*?)</div>', blob, re.I | re.S):
        t = re.sub(r"\s+", " ", strip_tags(m.group(1))).strip()
        if t and len(t) > 3 and "availabilityMoreDetailsIcon" not in t:
            avails.append(t)
    avail = " | ".join(avails[:2])
    if avail and re.search(
        r"currently unavailable|temporarily out of stock|(?<![a-z])out of stock(?![a-z])",
        avail,
        re.I,
    ):
        return False, "SOLD_OUT", f"amazon availability={avail[:100]!r}"

    ghost = bool(
        re.search(r'id=["\']buy-now-button["\']', blob, re.I)
        or re.search(r'id=["\']submit\.buy-now["\']', blob, re.I)
        or re.search(r"a-button-preorder", blob, re.I)
        or re.search(r"pre-?order now", avail, re.I)
        or re.search(r"will be released", avail, re.I)
    )
    if ghost:
        return (
            False,
            "SOLD_OUT",
            "amazon buy-now/preorder chrome without add-to-cart (ghost stock)",
        )
    if avail:
        return False, "SOLD_OUT", f"amazon no add-to-cart; availability={avail[:100]!r}"
    return False, "SOLD_OUT", "amazon no add-to-cart/pre-order submit on PDP"


def from_page(
    listing: Listing, html: str, url: str, asin: str = "", status: int = 200
) -> StockResult:
    if not (html or "").strip() or _looks_wall(html, status):
        return StockResult(
            listing,
            False,
            "ERROR",
            page_title(html),
            None,
            url,
            f"blocked or empty page (HTTP {status})",
            asin=asin,
        )
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
    ld = parse_json_ld(html or "")
    ld_price, ld_avail = _offer_fields(ld)
    if ld_price is not None:
        if price is None or abs(ld_price - MSRP[listing.item]) < abs((price or 0) - MSRP[listing.item]):
            price = ld_price
    n_price, n_avail, n_salable = (None, None, None)
    if listing.retailer == "nintendo":
        n_price, n_avail, n_salable = _nintendo_fields(html or "", listing.sku)
        if n_price is not None:
            try:
                price = float(n_price)
            except (TypeError, ValueError):
                pass

    cap = PRICE_CAP[listing.item]
    floor = PRICE_FLOOR[listing.item]
    blob = (html or "").lower()
    in_stock, status_s, reason = classify_blob(blob)
    bb_btn = _bestbuy_button(html or "", listing.sku) if listing.retailer == "bestbuy" else ""

    if listing.retailer == "amazon":
        in_stock, status_s, reason = _amazon_offer(html or "")
    elif listing.retailer == "nintendo" and n_avail is not None:
        avail_s = " ".join(n_avail) if isinstance(n_avail, list) else str(n_avail)
        coming = bool(re.search(r"coming soon", avail_s, re.I))
        if coming:
            in_stock, status_s, reason = False, "COMING_SOON", "nintendo availability coming soon"
        elif n_salable:
            in_stock, status_s, reason = True, "IN_STOCK", "nintendo isSalableQty=true"
        elif re.search(r"outofstock|out of stock", ld_avail, re.I):
            in_stock, status_s, reason = False, "SOLD_OUT", "json-ld OutOfStock"
        else:
            in_stock, status_s, reason = False, "SOLD_OUT", f"nintendo availability={avail_s!r}"
    elif bb_btn:
        if bb_btn == "COMING_SOON":
            in_stock, status_s, reason = False, "COMING_SOON", "bestbuy buttonState COMING_SOON"
        elif bb_btn in ("SOLD_OUT", "SOLD_OUT_ONLINE"):
            in_stock, status_s, reason = False, "SOLD_OUT", f"bestbuy buttonState {bb_btn}"
        elif bb_btn in ("ADD_TO_CART", "PRE_ORDER", "PREORDER"):
            in_stock, status_s, reason = True, "IN_STOCK", f"bestbuy buttonState {bb_btn}"
    elif ld_avail:
        if re.search(r"outofstock|out of stock", ld_avail, re.I):
            in_stock, status_s, reason = False, "SOLD_OUT", "json-ld OutOfStock"
        elif re.search(r"instock|in stock|preorder", ld_avail, re.I) and status_s not in (
            "SOLD_OUT",
            "COMING_SOON",
        ):
            in_stock, status_s, reason = True, "IN_STOCK", "json-ld InStock"

    if price is None and status_s in ("SOLD_OUT", "COMING_SOON"):
        price = MSRP[listing.item]
    if in_stock and price is None:
        in_stock, status_s, reason = False, "UNKNOWN", "buy signal but no product price"
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
    return StockResult(listing, in_stock, status_s, title, price, url, reason, asin=asin)
