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
from fndzlda.cart import add_to_cart_url, checkout_url, fire_browser, should_open_browser
from fndzlda.catalog import (
    CONSOLE,
    CONTROLLER,
    ITEM_LABEL,
    RETAILER_LABEL,
    SHOP_IDS,
    parse_shops,
)
from fndzlda.hunter import is_actionable, next_wait, scan
from fndzlda.notify import discord_stock, ping
from fndzlda.stock import StockResult
from fndzlda.update import check_and_apply

STATE_PATH = Path.home() / ".fndzlda" / "hits.json"
HIT_PAUSE = 120.0

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
    p.add_argument("--interval", type=float, default=20.0, help="seconds between misses (default 20)")
    p.add_argument(
        "--hit-wait",
        type=float,
        default=HIT_PAUSE,
        help="seconds to wait after a hit, then scan every store again (default 120)",
    )
    p.add_argument("--once", action="store_true", help="scan once and exit")
    p.add_argument("--dry-run", action="store_true", help="print cart/checkout URLs, do not open a browser")
    p.add_argument(
        "--again",
        action="store_true",
        help="open the cart again if the same listing is still in stock (default: once per hunt)",
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
    hunting = ", ".join(ITEM_LABEL[i] for i in (CONSOLE, CONTROLLER) if i in want)
    shop_names = " · ".join(RETAILER_LABEL[s] for s in SHOP_IDS if s in shops)
    print(f"  hunting  {hunting}")
    print(f"  shops    US only — {shop_names}")
    print(f"  miss wait {args.interval:.0f}s   hit wait {args.hit_wait:.0f}s")
    print("  Ctrl+C to quit. After a hit it waits two minutes, then scans every store again.")
    print("  Same listing is added to the cart once this hunt (use --again to add again).\n")

    # A new launch may add once. Do not reload yesterday's hits.json or a
    # real drop would not open the cart. Rescans in THIS run still skip.
    fired: set[str] = set()
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
            for hit in hits:
                k = _key(hit)
                shop = RETAILER_LABEL.get(hit.listing.retailer, hit.listing.retailer)
                kind = ITEM_LABEL[hit.listing.item]
                msg = f"{shop} has {kind}"
                cart_u = add_to_cart_url(hit.listing, hit.asin)
                check_u = checkout_url(hit.listing, hit.asin)
                # Always Discord on every actionable hit — even if cart already opened.
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
                # Box browser stays closed — Discord/chat carry buy links only.
                print(f"      -> {cart_u}")
                print(f"      -> {check_u}")
                print("      (no local browser open; Discord notification only)")
                ping("FndZlda", msg)
                if not args.dry_run:
                    fired.add(k)
                    _save_fired(fired)
            if args.once:
                return 0
            wait = next_wait(len(hits), args.interval, args.hit_wait)
            if hits:
                print(f"  hit. waiting {wait:.0f}s, then scanning every chosen store again. Ctrl+C to quit.\n")
            else:
                print(f"  next scan in {wait:.0f}s\n")
            time.sleep(wait)
    except KeyboardInterrupt:
        print("\n  stopped. (Ganon can wait.)")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
