"""Small urllib wrapper with a browser-like UA. Falls back to curl when shops block us."""
from __future__ import annotations

import gzip
import shutil
import ssl
import subprocess
import urllib.error
import urllib.request
from dataclasses import dataclass

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)
# Chrome UA is RST by Akamai on www.bestbuy.com; the store app UA is not.
BB_UA = "BestBuy/21.11.0 (iPhone; iOS 18.0; Scale/3.00)"

HEADERS = {
    "User-Agent": UA,
    "Accept": "text/html,application/json,application/xhtml+xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "Cache-Control": "no-cache",
    "Referer": "https://www.google.com/",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
}

_WALL = (
    "attention required",
    "cloudflare",
    "captcha",
    "automated access",
    "sorry! something went wrong",
    "to discuss automated access",
    "enable javascript and cookies",
)


@dataclass
class FetchResult:
    url: str
    status: int
    body: str
    error: str = ""


def _decode(raw: bytes, headers) -> str:
    enc = ""
    try:
        enc = (headers.get("Content-Encoding") or "").lower()
    except Exception:
        enc = ""
    if raw[:2] == b"\x1f\x8b" or "gzip" in enc:
        try:
            raw = gzip.decompress(raw)
        except Exception:
            pass
    charset = "utf-8"
    try:
        ctype = headers.get_content_charset()
        if ctype:
            charset = ctype
    except Exception:
        pass
    return raw.decode(charset, "replace")


def _is_wall(status: int, body: str) -> bool:
    if not (body or "").strip():
        return True
    if status in (0, 403, 429, 503):
        if len(body) < 8000:
            return True
        blob = body.lower()
        return any(w in blob for w in _WALL)
    blob = body.lower()
    return any(w in blob for w in ("to discuss automated access", "attention required! | cloudflare"))


def _fetch_urllib(url: str, timeout: float, ua: str | None = None) -> FetchResult:
    headers = dict(HEADERS)
    if ua:
        headers["User-Agent"] = ua
    req = urllib.request.Request(url, headers=headers)
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            raw = resp.read()
            body = _decode(raw, resp.headers)
            return FetchResult(url=resp.geturl() or url, status=int(resp.status), body=body)
    except urllib.error.HTTPError as e:
        raw = b""
        try:
            raw = e.read() or b""
        except Exception:
            pass
        body = _decode(raw, e.headers or {})
        return FetchResult(url=url, status=int(e.code), body=body, error=f"HTTP {e.code}")
    except Exception as e:
        return FetchResult(url=url, status=0, body="", error=f"{type(e).__name__}: {e}")


def _fetch_curl(url: str, timeout: float, ua: str | None = None) -> FetchResult | None:
    curl = shutil.which("curl") or shutil.which("curl.exe")
    if not curl:
        return None
    cmd = [
        curl,
        "-sS",
        "-L",
        "--compressed",
        "--max-time",
        str(max(3, int(timeout))),
        "-A",
        ua or UA,
        "-H",
        "Accept: text/html,application/json,application/xhtml+xml;q=0.9,*/*;q=0.8",
        "-H",
        "Accept-Language: en-US,en;q=0.9",
        "-H",
        "Referer: https://www.google.com/",
        "-H",
        "Sec-Fetch-Dest: document",
        "-H",
        "Sec-Fetch-Mode: navigate",
        "-H",
        "Sec-Fetch-Site: none",
        "-H",
        "Upgrade-Insecure-Requests: 1",
        "-w",
        "\n__FNDZLDA_HTTP__:%{http_code}",
        url,
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, timeout=timeout + 4)
    except Exception as e:
        return FetchResult(url=url, status=0, body="", error=f"curl {type(e).__name__}: {e}")
    raw = proc.stdout or b""
    text = raw.decode("utf-8", "replace")
    status = 0
    if "__FNDZLDA_HTTP__:" in text:
        body, _, tail = text.rpartition("__FNDZLDA_HTTP__:")
        try:
            status = int(tail.strip().split()[0])
        except (ValueError, IndexError):
            status = 0
        text = body.rstrip("\n")
    stderr = (proc.stderr or b"").decode("utf-8", "replace").strip()
    # curl writes http_code 000 on timeouts and HTTP/2 RSTs. Do not coerce that to 200.
    if proc.returncode != 0 or not status:
        err = stderr or f"curl exit {proc.returncode}"
        return FetchResult(url=url, status=0, body=text, error=err)
    err = ""
    if status >= 400:
        err = f"HTTP {status}"
    return FetchResult(url=url, status=status, body=text, error=err)


def _bestbuy_error(err: str) -> str:
    blob = err or ""
    if "HTTP/2 stream" in blob or "INTERNAL_ERROR" in blob:
        return "blocked by Best Buy (Akamai HTTP/2 reset)"
    if "timed out" in blob.lower() or "timeout" in blob.lower():
        return "blocked by Best Buy (Akamai timeout)"
    return blob or "blocked by Best Buy"


def fetch(url: str, timeout: float = 12.0) -> FetchResult:
    if "bestbuy.com" in url.lower():
        via_curl = _fetch_curl(url, min(timeout, 10.0), ua=BB_UA)
        if via_curl and not _is_wall(via_curl.status, via_curl.body):
            return via_curl
        # Chrome UA is RST; if the store-app UA also dies, urllib will just hang.
        if via_curl and (via_curl.status == 0 or not (via_curl.body or "").strip()):
            return FetchResult(
                url=via_curl.url,
                status=0,
                body=via_curl.body,
                error=_bestbuy_error(via_curl.error),
            )
        page = _fetch_urllib(url, timeout, ua=BB_UA)
        if not _is_wall(page.status, page.body):
            return page
        return via_curl or page

    page = _fetch_urllib(url, timeout)
    if not _is_wall(page.status, page.body):
        return page
    via_curl = _fetch_curl(url, timeout)
    if via_curl and not _is_wall(via_curl.status, via_curl.body):
        return via_curl
    return via_curl or page
