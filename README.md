# FndZlda

Terminal hunter for the **Nintendo Switch 2 – The Legend of Zelda – 40th Anniversary Edition** console and the matching **Pro Controller**.

Runs on **Linux** and **Windows** (Python 3.10+, stdlib only). On a real in-stock hit it opens your **default browser** to the retailer’s add-to-cart link, then checkout.

Startup is the N64 **Ocarina of Time** title card, in terminal art.

## Hunt

```text
python -m fndzlda
```

It asks:

1. Console only ($519.99)
2. Zelda Pro Controller ($99.99)
3. Both

Then it scans, on a polite interval:

| Shop | Console | Pro Controller |
|---|---|---|
| Nintendo | SKU 121642 | SKU 127074 |
| Best Buy | 6691841 | 6691849 |
| Target | TCIN 1013322047 | 1013213521 |
| Walmart | 21002656445 | 20954470204 |
| GameStop | 20037854 | 20037855 |
| Amazon | UPC 045496885434 | 045496886325 |

A listing is treated as buyable only when **all** of these hold:

- The page is the Zelda **40th** Switch **2** SKU (PowerA, OLED, carrying case, amiibo are rejected)
- A buy / pre-order signal beats sold-out / coming-soon
- Price is under a cap so marketplace scalpers do not fire the browser

On a hit: beep, desktop ping if available, **add to cart** URL, then **checkout** URL in the default browser. The same shop+SKU is not opened twice unless you pass `--again`.

## Flags

```text
python -m fndzlda --want both
python -m fndzlda --want console --once --dry-run
python -m fndzlda --want controller --interval 15
python -m fndzlda --no-banner
```

| Flag | Meaning |
|---|---|
| `--want console\|controller\|both` | Skip the prompt |
| `--interval N` | Seconds between scans (default 20) |
| `--once` | One pass, then exit |
| `--dry-run` | Print cart/checkout URLs, do not open a browser |
| `--again` | Fire even if this listing already hit |

Windows: `py -3 -m fndzlda` from this folder, or `fndzlda.cmd`.

You still need to be signed in at that shop for checkout to complete. Nintendo in particular will not add to cart from a cold GET; the product page is opened so you can finish the click.

## Install

No third-party packages.

```text
git clone https://github.com/Memberoffoxhound/FndZlda.git
cd FndZlda
python -m fndzlda
```

```text
python -m unittest discover -s tests -v
```
