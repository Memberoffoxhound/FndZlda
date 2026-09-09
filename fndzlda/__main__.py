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
from fndzlda.cart import fire_browser
from fndzlda.catalog import CONSOLE, CONTROLLER, ITEM_LABEL, RETAILER_LABEL
from fndzlda.hunter import is_actionable, scan
from fndzlda.notify import ping
from fndzlda.stock import StockResult

STATE_PATH = Path.home() / ".fndzlda" / "hits.json"

PROMPT = """
Hunt which US Zelda 40th Anniversary Switch 2 items?

  [1] Console only          ($519.99)
  [2] Zelda Pro Controller  ($99.99)
  [3] Both

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


def _load_fired() -> set[str]:
    try:
        data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        return set(data.get("fired") or [])
    except Exception:
        return set()


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
    }.get(hit.status, hit.status)
    if hit.in_stock:
        flag = f"\033[1;32m{flag}\033[0m"
    elif hit.status == "SOLD_OUT":
        flag = f"\033[31m{flag}\033[0m"
    elif hit.status == "ERROR":
        flag = f"\033[33m{flag}\033[0m"
    return f"  {shop:<10}  {kind:<28}  {flag}{price}"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="fndzlda",
        description="Hunt the US Zelda 40th Switch 2 console and Pro Controller (US retailers only).",
    )
    p.add_argument("--want", help="console | controller | both  (skips the prompt)")
    p.add_argument("--interval", type=float, default=20.0, help="seconds between scans (default 20)")
    p.add_argument("--once", action="store_true", help="scan once and exit")
    p.add_argument("--dry-run", action="store_true", help="print cart/checkout URLs, do not open a browser")
    p.add_argument("--again", action="store_true", help="fire the browser even if this listing already hit")
    p.add_argument("--workers", type=int, default=6)
    p.add_argument("--no-banner", action="store_true")
    p.add_argument("--version", action="version", version=f"FndZlda {__version__}")
    args = p.parse_args(argv)

    if not args.no_banner:
        print_logo()

    want = _ask_want(args.want)
    hunting = ", ".join(ITEM_LABEL[i] for i in (CONSOLE, CONTROLLER) if i in want)
    print(f"  hunting  {hunting}")
    print(f"  shops    US only — Nintendo · Best Buy · Target · Walmart · GameStop · Amazon")
    print(f"  interval {args.interval:.0f}s   (q + enter to quit between scans)\n")

    fired = set() if args.again else _load_fired()
    scans = 0
    try:
        while True:
            scans += 1
            stamp = time.strftime("%H:%M:%S")
            print(f"\u2500\u2500 scan {scans}  {stamp} \u2500\u2500")
            results = scan(want, workers=args.workers)
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
                if k in fired:
                    print(f"  already opened browser for {msg}")
                    continue
                print()
                print(hey_listen())
                print(f"  *** HIT  {msg}  ***")
                if hit.title:
                    print(f"      {hit.title}")
                ping("FndZlda", msg)
                urls = fire_browser(hit, dry_run=args.dry_run)
                for u in urls:
                    print(f"      -> {u}")
                if not args.dry_run:
                    print("      default browser: add-to-cart, then checkout")
                fired.add(k)
                _save_fired(fired)
            if args.once:
                return 0
            print(f"  next scan in {args.interval:.0f}s\n")
            time.sleep(max(3.0, args.interval))
    except KeyboardInterrupt:
        print("\n  stopped. (Ganon can wait.)")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
