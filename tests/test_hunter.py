import unittest

from fndzlda.catalog import CONSOLE
from fndzlda.httputil import FetchResult
from fndzlda.hunter import is_actionable, scan


class TestScan(unittest.TestCase):
    def test_scan_uses_injected_fetch(self):
        html = (
            "<title>Nintendo Switch 2 The Legend of Zelda 40th Anniversary Edition</title>"
            "Add to cart $519.99"
        )

        def getter(url: str) -> FetchResult:
            return FetchResult(url=url, status=200, body=html)

        rows = scan({CONSOLE}, workers=2, getter=getter)
        self.assertGreaterEqual(len(rows), 5)
        shops = {r.listing.retailer for r in rows}
        self.assertIn("bestbuy", shops)
        self.assertTrue(any(is_actionable(r) for r in rows if r.listing.retailer != "amazon"))
