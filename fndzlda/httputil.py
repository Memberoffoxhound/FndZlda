"""Small urllib wrapper with a browser-like UA. No third-party deps."""
from __future__ import annotations

import gzip
import ssl
import urllib.error
import urllib.request
from dataclasses import dataclass

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)

HEADERS = {
    "User-Agent": UA,
    "Accept": "text/html,application/json,application/xhtml+xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "Cache-Control": "no-cache",
}


@dataclass
class FetchResult:
    url: str
    status: int
    body: str
    error: str = ""


def fetch(url: str, timeout: float = 12.0) -> FetchResult:
    req = urllib.request.Request(url, headers=HEADERS)
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            raw = resp.read()
            if resp.headers.get("Content-Encoding", "").lower() == "gzip":
                try:
                    raw = gzip.decompress(raw)
                except Exception:
                    pass
            charset = "utf-8"
            ctype = resp.headers.get_content_charset()
            if ctype:
                charset = ctype
            body = raw.decode(charset, "replace")
            return FetchResult(url=resp.geturl() or url, status=int(resp.status), body=body)
    except urllib.error.HTTPError as e:
        raw = b""
        try:
            raw = e.read() or b""
        except Exception:
            pass
        body = raw.decode("utf-8", "replace")
        return FetchResult(url=url, status=int(e.code), body=body, error=f"HTTP {e.code}")
    except Exception as e:
        return FetchResult(url=url, status=0, body="", error=f"{type(e).__name__}: {e}")
