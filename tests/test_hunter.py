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

    def test_scan_respects_shops(self):
        html = (
            "<title>Nintendo Switch 2 The Legend of Zelda 40th Anniversary Edition</title>"
            "Add to cart $519.99"
        )

        def getter(url: str) -> FetchResult:
            return FetchResult(url=url, status=200, body=html)

        rows = scan({CONSOLE}, workers=2, getter=getter, shops={"walmart", "target"})
        shops = {r.listing.retailer for r in rows}
        self.assertEqual(shops, {"walmart", "target"})

    def test_next_wait_is_two_minutes_after_a_hit(self):
        from fndzlda.hunter import next_wait

        self.assertEqual(next_wait(1, 20.0), 120.0)
        self.assertEqual(next_wait(0, 20.0), 20.0)

    def test_bestbuy_transport_error_is_error_not_wrong_item(self):
        def getter(url: str) -> FetchResult:
            return FetchResult(
                url=url, status=0, body="", error="blocked by Best Buy (Akamai HTTP/2 reset)"
            )

        rows = scan({CONSOLE}, workers=1, getter=getter, shops={"bestbuy"})
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].status, "ERROR")
        self.assertIn("Akamai", rows[0].reason)
        self.assertFalse(is_actionable(rows[0]))
