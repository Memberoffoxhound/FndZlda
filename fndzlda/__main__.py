#!/usr/bin/env python3
"""FndZlda — hunt the Zelda 40th Anniversary Switch 2 console and Pro Controller."""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from fndzlda import __version__
from fndzlda.banner import disappointment, hey_listen, print_logo
from fndzlda.cart import add_to_cart_url, checkout_url, fire_browser
from fndzlda.catalog import (
    CONSOLE,
    CONTROLLER,
    ITEM_LABEL,
    RETAILER_LABEL,
    SHOP_IDS,
    parse_shops,
)
from fndzlda.hunter import (
    is_actionable,
    mark_shop_cooldown,
    next_wait,
    scan,
    shop_cooldown_left,
)
from fndzlda.notify import discord_stock, ping
from fndzlda.stock import StockResult
from fndzlda.update import check_and_apply

STATE_PATH = Path.home() / ".fndzlda" / "hits.json"
HIT_PAUSE = 120.0
DEFAULT_INTERVAL = 20.0

PROMPT = """
Hunt which US Zelda 40th Anniversary Switch 2 items?

  [1] Console only          ($519.99)
  [2] Zelda Pro Controller  ($99.99)
  [3] Both

> """

SHOP_PROMPT = """
Which US stores should I check?

Type the names, separated by commas. Spelling can be messy.
Stores: Nintendo, Best Buy, Target, Walmart, GameStop, Amazon
Type all if you want every store.

Examples:  walmart, target
           best buy, gamestop, amazon
           all

> """

INTERVAL_PROMPT = """
How many seconds between scans?

Type a number in 5 second steps:  5  10  15  20  25  30  …
Press Enter for 20.

> """


def snap_interval(seconds: float) -> float:
    n = int(round(float(seconds) / 5.0) * 5)
    return float(min(300, max(5, n)))


def _ask_want(preset: str | None) -> set[str]:
    if preset in ("console", "1"):
        return {CONSOLE}
    if preset in ("controller", "pro", "2"):
        return {CONTROLLER}
    if preset in ("both", "3"):
        return {CONSOLE, CONTROLLER}
    if preset:
        print(f"unknown --want {preset!r}; use console, controller, or both", file=sys.stderr)
        sys.exit(2)
    while True:
        try:
            raw = input(PROMPT).strip().lower()
        except EOFError:
            print("\nneed a choice (1/2/3)", file=sys.stderr)
            sys.exit(2)
        if raw in ("1", "console", "c"):
            return {CONSOLE}
        if raw in ("2", "controller", "pro", "p"):
            return {CONTROLLER}
        if raw in ("3", "both", "b"):
            return {CONSOLE, CONTROLLER}
        print("  type 1, 2, or 3")


def _ask_shops(preset: str | None) -> set[str]:
    if preset:
        shops, unknown = parse_shops(preset)
        if unknown or not shops:
            print(
                f"unknown --shops {preset!r}; use nintendo, bestbuy, target, walmart, gamestop, amazon, or all",
                file=sys.stderr,
            )
            sys.exit(2)
        return shops
    while True:
        try:
            raw = input(SHOP_PROMPT).strip()
        except EOFError:
            print("\nneed a store list (or all)", file=sys.stderr)
            sys.exit(2)
        shops, unknown = parse_shops(raw)
        if unknown:
            print("  I didn't get: " + ", ".join(unknown))
            print("  try: nintendo, best buy, target, walmart, gamestop, amazon  (or all)")
            continue
        if not shops:
            print("  type store names, separated by commas. or type all")
            continue
        return shops


def _ask_interval(preset: float | None) -> float:
    if preset is not None:
        return snap_interval(preset)
    while True:
        try:
            raw = input(INTERVAL_PROMPT).strip().lower()
        except EOFError:
            return DEFAULT_INTERVAL
        if not raw or raw in ("d", "default", "enter"):
            return DEFAULT_INTERVAL
        try:
            val = float(raw.replace("s", "").replace("sec", "").replace("onds", ""))
        except ValueError:
            print("  type a number like 5, 10, 15, or 20")
            continue
        if val <= 0:
            print("  need a number of seconds, 5 or more")
            continue
        snapped = snap_interval(val)
        if snapped != val:
            print(f"  using {snapped:.0f}s (5 second steps)")
        return snapped


def _save_fired(keys: set[str]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps({"fired": sorted(keys)}, indent=2), encoding="utf-8")


def _key(hit: StockResult) -> str:
    return f"{hit.listing.retailer}:{hit.listing.item}:{hit.listing.sku}:{hit.asin}"


def _paint(hit: StockResult) -> str:
    shop = RETAILER_LABEL.get(hit.listing.retailer, hit.listing.retailer)
    kind = ITEM_LABEL[hit.listing.item]
    price = f"  ${hit.price:.2f}" if hit.price else ""
    flag = {
        "IN_STOCK": "IN STOCK",
        "SOLD_OUT": "sold out",
        "UNKNOWN": "unknown",
        "WRONG_ITEM": "wrong item",
        "SCALPER": "scalper price",
        "WRONG_PRICE": "wrong price",
        "ERROR": "error",
        "COMING_SOON": "coming soon",
    }.get(hit.status, hit.status)
    if hit.in_stock:
        flag = f"\033[1;32m{flag}\033[0m"
    elif hit.status == "SOLD_OUT":
        flag = f"\033[31m{flag}\033[0m"
    elif hit.status == "COMING_SOON":
        flag = f"\033[33m{flag}\033[0m"
    elif hit.status == "ERROR":
        flag = f"\033[33m{flag}\033[0m"
    return f"  {shop:<10}  {kind:<28}  {flag}{price}"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="fndzlda",
        description="Hunt the US Zelda 40th Switch 2 console and Pro Controller (US retailers only).",
    )
    p.add_argument("--want", help="console | controller | both  (skips the item prompt)")
    p.add_argument(
        "--shops",
        help="comma-separated stores, or all  (skips the store prompt). typos are ok",
    )
    p.add_argument(
        "--interval",
        type=float,
        default=None,
        help="seconds between scans (5 second steps). skips the interval question",
    )
    p.add_argument(
        "--hit-wait",
        type=float,
        default=HIT_PAUSE,
        help="per-store auto-add cooldown in seconds (default 120). other shops keep scanning",
    )
    p.add_argument("--once", action="store_true", help="scan once and exit")
    p.add_argument("--dry-run", action="store_true", help="print cart/checkout URLs, do not open a browser")
    p.add_argument(
        "--again",
        action="store_true",
        help="ignore the per-store auto-add cooldown and open the cart on every hit",
    )
    p.add_argument("--workers", type=int, default=6)
    p.add_argument("--no-banner", action="store_true")
    p.add_argument(
        "--no-update",
        action="store_true",
        help="skip the GitHub latest-commit check",
    )
    p.add_argument("--version", action="version", version=f"FndZlda {__version__}")
    args = p.parse_args(argv)

    if not args.no_update:
        rest = list(argv) if argv is not None else sys.argv[1:]
        check_and_apply(argv=rest)

    if not args.no_banner:
        print_logo()

    want = _ask_want(args.want)
    shops = _ask_shops(args.shops)
    interval = _ask_interval(args.interval)
    hunting = ", ".join(ITEM_LABEL[i] for i in (CONSOLE, CONTROLLER) if i in want)
    shop_names = " · ".join(RETAILER_LABEL[s] for s in SHOP_IDS if s in shops)
    print(f"  hunting  {hunting}")
    print(f"  shops    US only — {shop_names}")
    print(f"  scan every {interval:.0f}s   auto-add cooldown {args.hit_wait:.0f}s per store")
    print("  Ctrl+C to quit. Hits notify every time. Auto-add cools only that store.")
    print("  Best Buy opens the Pre-Order / add-to-cart button (queue or cart).\n")

    fired: set[str] = set()
    shop_until: dict[str, float] = {}
    scans = 0
    try:
        while True:
            scans += 1
            stamp = time.strftime("%H:%M:%S")
            print(f"── scan {scans}  {stamp} ──")
            results = scan(want, workers=args.workers, shops=shops)
            hits: list[StockResult] = []
            for hit in results:
                print(_paint(hit))
                if is_actionable(hit):
                    hits.append(hit)
            if not hits:
                print(disappointment(scans))
            opened_shops: set[str] = set()
            now = time.monotonic()
            for hit in hits:
                k = _key(hit)
                retailer = hit.listing.retailer
                shop = RETAILER_LABEL.get(retailer, retailer)
                kind = ITEM_LABEL[hit.listing.item]
                msg = f"{shop} has {kind}"
                cart_u = add_to_cart_url(hit.listing, hit.asin)
                check_u = checkout_url(hit.listing, hit.asin)
                print()
                print(hey_listen())
                print(f"  *** HIT  {msg}  ***")
                if hit.title:
                    print(f"      {hit.title}")
                if discord_stock(
                    "HEY! LISTEN!!! Stock found",
                    msg,
                    product_url=hit.url or hit.listing.url,
                    cart_url=cart_u,
                    checkout_url=check_u,
                    price=hit.price,
                ):
                    print("      posted to Discord #find-zelda")
                else:
                    print("      Discord post failed or webhook missing")
                left = 0.0 if args.again else shop_cooldown_left(retailer, shop_until, now=now)
                if left > 0:
                    print(f"  {shop} auto-add cooling {left:.0f}s — notified, not opening cart")
                    print(f"      -> {cart_u}")
                    print(f"      -> {check_u}")
                    continue
                ping("FndZlda", msg)
                urls = fire_browser(hit, dry_run=args.dry_run, again=True)
                for u in urls:
                    print(f"      -> {u}")
                if retailer == "bestbuy" and not args.dry_run:
                    print("      Best Buy: Pre-Order / add-to-cart (queue or cart)")
                elif not args.dry_run:
                    print("      default browser: add-to-cart, then checkout")
                fired.add(k)
                opened_shops.add(retailer)
                _save_fired(fired)
            for retailer in opened_shops:
                mark_shop_cooldown(retailer, shop_until, args.hit_wait, now=now)
            if args.once:
                return 0
            wait = next_wait(len(hits), interval, args.hit_wait)
            print(f"  next scan in {wait:.0f}s\n")
            time.sleep(wait)
    except KeyboardInterrupt:
        print("\n  stopped. (Ganon can wait.)")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
