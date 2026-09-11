"""Open the default browser to add-to-cart / pre-order, then checkout.

Best Buy: open the product page, click yellow Pre-Order via UI Automation,
and if a Sold Out dialog appears, hit Close and retry up to `tries`.
Fallback is the skuId add-to-cart URL if the button cannot be seen.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import time
import webbrowser
from pathlib import Path

from fndzlda.catalog import Listing
from fndzlda.stock import StockResult

_opened_carts: set[str] = set()

_BB_PS = r"""
Add-Type -AssemblyName UIAutomationClient
$root = [System.Windows.Automation.AutomationElement]::RootElement
function Find-Named($names) {
  foreach ($n in $names) {
    $c = New-Object System.Windows.Automation.PropertyCondition(
      [System.Windows.Automation.AutomationElement]::NameProperty, $n)
    $el = $root.FindFirst([System.Windows.Automation.TreeScope]::Descendants, $c)
    if ($el) { return $el }
  }
  return $null
}
function Invoke-El($el) {
  if (-not $el) { return $false }
  try {
    $p = $el.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern)
    $p.Invoke()
    return $true
  } catch { return $false }
}
$closed = Invoke-El (Find-Named @('Close','close','CLOSE','Dismiss','OK','Ok'))
Start-Sleep -Milliseconds 250
$clicked = Invoke-El (Find-Named @(
  'Pre-Order','Pre-order','Preorder','PRE-ORDER',
  'Pre-Order Now','Add to Cart','Add to cart','Add To Cart'
))
if ($clicked) { Write-Output 'clicked' }
elseif ($closed) { Write-Output 'closed' }
else { Write-Output 'miss' }
"""


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


def _bb_click_pass() -> str:
    if sys.platform != "win32":
        return "skip"
    script = Path(tempfile.gettempdir()) / "fndzlda-bb-click.ps1"
    try:
        script.write_text(_BB_PS, encoding="utf-8")
        proc = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(script),
            ],
            capture_output=True,
            text=True,
            timeout=8,
        )
    except Exception:
        return "err"
    text = ((proc.stdout or "") + " " + (proc.stderr or "")).lower()
    if "clicked" in text:
        return "clicked"
    if "closed" in text:
        return "closed"
    return "miss"


def fire_browser(
    hit: StockResult,
    delay_s: float = 2.2,
    dry_run: bool = False,
    again: bool = False,
    tries: int = 1,
) -> list[str]:
    cart = add_to_cart_url(hit.listing, hit.asin)
    check = checkout_url(hit.listing, hit.asin)
    burst = max(1, int(tries))
    if hit.listing.retailer == "bestbuy":
        planned = [check, cart] * burst
    else:
        planned = [cart] if check == cart else [cart, check]
    if dry_run:
        return planned
    if cart in _opened_carts and not again:
        return []
    _opened_carts.add(cart)
    if hit.listing.retailer == "bestbuy":
        page = check or hit.listing.url or cart
        webbrowser.open(page, new=2)
        time.sleep(1.2)
        for i in range(burst):
            result = _bb_click_pass()
            if result == "clicked":
                print(f"      Best Buy Pre-Order click {i + 1}/{burst}")
            elif result == "closed":
                print(f"      Best Buy sold-out Close {i + 1}/{burst} — retrying")
                time.sleep(0.35)
                _bb_click_pass()
            else:
                webbrowser.open(cart, new=2)
                print(f"      Best Buy Pre-Order URL {i + 1}/{burst} (button not seen)")
            if i + 1 < burst:
                time.sleep(0.9)
        return planned
    webbrowser.open(cart, new=2)
    if check != cart:
        time.sleep(max(0.4, delay_s))
        webbrowser.open(check, new=2)
    return planned
