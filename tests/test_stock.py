import unittest

from fndzlda.catalog import CONSOLE, CONTROLLER, Listing
from fndzlda.stock import classify_blob, from_page, pick_amazon_asin


class TestClassify(unittest.TestCase):
    def test_sold_out_beats_add_to_list(self):
        html = "preorders have sold out. add to list. notify me when available"
        ok, status, _ = classify_blob(html)
        self.assertFalse(ok)
        self.assertEqual(status, "SOLD_OUT")

    def test_add_to_cart(self):
        ok, status, _ = classify_blob('{"buttonState":"ADD_TO_CART","purchasable":true}')
        self.assertTrue(ok)
        self.assertEqual(status, "IN_STOCK")

    def test_preorder_now(self):
        ok, status, _ = classify_blob("Pre-order now \u00b7 ships October 29")
        self.assertTrue(ok)


class TestFromPage(unittest.TestCase):
    listing = Listing(
        "bestbuy",
        CONSOLE,
        "6691841",
        "https://www.bestbuy.com/product/x/sku/6691841",
    )

    def test_wrong_item(self):
        html = "<title>PowerA Zelda Wired Controller</title> Add to cart $29.99"
        hit = from_page(self.listing, html, self.listing.url)
        self.assertFalse(hit.in_stock)
        self.assertEqual(hit.status, "WRONG_ITEM")

    def test_in_stock_console(self):
        html = (
            "<title>Switch 2 \u2013 The Legend of Zelda \u2013 40th Anniversary Edition - Best Buy</title>"
            'sku 6691841 {"buttonState":"ADD_TO_CART"} $519.99'
        )
        hit = from_page(self.listing, html, self.listing.url)
        self.assertTrue(hit.in_stock)
        self.assertEqual(hit.price, 519.99)

    def test_protection_plan_price_is_not_the_console(self):
        html = (
            "<title>Nintendo Switch 2 The Legend of Zelda 40th Anniversary Edition Console System : Target</title>"
            "Add to cart $35.00  2 Year Video Games Protection Plan"
        )
        hit = from_page(self.listing, html, self.listing.url)
        self.assertFalse(hit.in_stock)
        self.assertEqual(hit.status, "WRONG_PRICE")

    def test_scalper_price(self):
        html = (
            "<title>Nintendo Switch 2 The Legend of Zelda 40th Anniversary Edition</title>"
            "Add to cart $849.00"
        )
        hit = from_page(self.listing, html, self.listing.url)
        self.assertFalse(hit.in_stock)
        self.assertEqual(hit.status, "SCALPER")


class TestAmazonPick(unittest.TestCase):
    def test_picks_matching_asin(self):
        html = (
            'data-asin="B0TEST0001"><img alt="PowerA Zelda Controller">'
            'data-asin="B0ZLDA40TH"><img alt="Nintendo Switch 2 The Legend of Zelda 40th Anniversary Edition">'
        )
        asin, title = pick_amazon_asin(html, CONSOLE)
        self.assertEqual(asin, "B0ZLDA40TH")
        self.assertIn("Zelda", title)
