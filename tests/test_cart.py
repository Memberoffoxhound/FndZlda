import unittest
from unittest.mock import patch

from fndzlda.cart import (
    add_to_cart_url,
    checkout_url,
    fire_browser,
    reset_opened_carts,
    should_open_browser,
)
from fndzlda.catalog import CONSOLE, CONTROLLER, listings_for
from fndzlda.stock import StockResult


class TestCartUrls(unittest.TestCase):
    def test_bestbuy_preorder_button_url(self):
        row = next(x for x in listings_for({CONSOLE}) if x.retailer == "bestbuy")
        cart = add_to_cart_url(row)
        self.assertIn("skuId=6691841", cart)
        self.assertIn("/cart/r/add-to-cart", cart)
        self.assertEqual(checkout_url(row), row.url)
        self.assertIn("/product/", checkout_url(row))

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

    def test_should_open_browser_once_unless_again(self):
        opened = {"bestbuy:console:6691841:"}
        self.assertFalse(should_open_browser("bestbuy:console:6691841:", opened))
        self.assertTrue(should_open_browser("bestbuy:console:6691841:", opened, again=True))
        self.assertTrue(should_open_browser("bestbuy:controller:6691849:", opened))

    def test_bestbuy_add_to_cart_opens_once(self):
        reset_opened_carts()
        row = next(x for x in listings_for({CONSOLE}) if x.retailer == "bestbuy")
        hit = StockResult(row, True, "IN_STOCK", "x", 519.99, row.url, "test")
        with patch("fndzlda.cart.webbrowser.open") as open_tab, patch("fndzlda.cart.time.sleep"):
            first = fire_browser(hit, delay_s=0.4)
            second = fire_browser(hit, delay_s=0.4)
            third = fire_browser(hit, delay_s=0.4, again=True)
        self.assertGreaterEqual(len(first), 1)
        self.assertIn("/cart/r/add-to-cart", first[0])
        self.assertEqual(second, [])
        self.assertGreaterEqual(len(third), 1)
        cart = add_to_cart_url(row)
        cart_opens = [c for c in open_tab.call_args_list if c.args and c.args[0] == cart]
        self.assertEqual(len(cart_opens), 2)
        reset_opened_carts()
