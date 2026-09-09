import unittest

from fndzlda.cart import add_to_cart_url, checkout_url, fire_browser
from fndzlda.catalog import CONSOLE, CONTROLLER, listings_for
from fndzlda.stock import StockResult


class TestCartUrls(unittest.TestCase):
    def test_bestbuy_click_cart(self):
        row = next(x for x in listings_for({CONSOLE}) if x.retailer == "bestbuy")
        self.assertIn("/6691841/cart", add_to_cart_url(row))
        self.assertIn("checkout", checkout_url(row))

    def test_amazon_asin(self):
        row = next(x for x in listings_for({CONSOLE}) if x.retailer == "amazon")
        url = add_to_cart_url(row, asin="B0ABCDEF12")
        self.assertIn("ASIN.1=B0ABCDEF12", url)

    def test_dry_run_does_not_need_browser(self):
        row = next(x for x in listings_for({CONTROLLER}) if x.retailer == "walmart")
        hit = StockResult(row, True, "IN_STOCK", "x", 99.0, row.url, "test")
        urls = fire_browser(hit, dry_run=True)
        self.assertEqual(len(urls), 2)
        self.assertIn("walmart.com", urls[0])
