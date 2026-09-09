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
        ok, status, _ = classify_blob("Pre-order now · ships October 29")
        self.assertTrue(ok)

    def test_disabled_add_to_cart_is_sold_out(self):
        ok, status, _ = classify_blob('<button type="button" disabled="">Add to cart</button>')
        self.assertFalse(ok)
        self.assertEqual(status, "SOLD_OUT")


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
            "<title>Switch 2 – The Legend of Zelda – 40th Anniversary Edition - Best Buy</title>"
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

    def test_json_price_beats_related_99(self):
        html = (
            "<title>Nintendo Switch 2 The Legend of Zelda 40th Anniversary Edition</title>"
            'preorders have sold out "finalPrice":519.99 "regularPrice":519.99 $99.99'
        )
        hit = from_page(self.listing, html, self.listing.url)
        self.assertEqual(hit.price, 519.99)
        self.assertEqual(hit.status, "SOLD_OUT")

    def test_soldoutpermanent_is_not_sold_out(self):
        html = (
            "<title>Nintendo Switch 2 The Legend of Zelda 40th Anniversary Edition</title>"
            'Add to cart $519.99 "soldOutPermanent":null'
        )
        hit = from_page(self.listing, html, self.listing.url)
        self.assertTrue(hit.in_stock)
        self.assertEqual(hit.status, "IN_STOCK")
        self.assertEqual(hit.price, 519.99)

    def test_cloudflare_wall_is_error_not_wrong_item(self):
        html = "<title>Attention Required! | Cloudflare</title><p>captcha</p>"
        hit = from_page(self.listing, html, self.listing.url, status=403)
        self.assertEqual(hit.status, "ERROR")
        self.assertFalse(hit.in_stock)

    def test_walmart_perimeterx_412_is_error_not_wrong_item(self):
        html = (
            '{"redirectUrl":"/blocked?url=Lw==","appId":"PXu6b0qd2S",'
            '"jsClientSrc":"/px/PXu6b0qd2S/init.js",'
            '"blockScript":"/px/PXu6b0qd2S/captcha/captcha.js?a=c"}'
        )
        listing = Listing(
            "walmart",
            CONSOLE,
            "21002656445",
            "https://www.walmart.com/ip/Nintendo-Switch-2-The-Legend-of-Zelda-40th-Anniversary-Edition/21002656445",
        )
        hit = from_page(listing, html, listing.url, status=412)
        self.assertEqual(hit.status, "ERROR")
        self.assertFalse(hit.in_stock)
        self.assertIn("412", hit.reason)

    def test_nintendo_coming_soon_is_not_a_hit(self):
        html = (
            "<title>Nintendo Switch 2 Pro Controller The Legend of Zelda 40th Anniversary Edition</title>"
            '<script id="__NEXT_DATA__" type="application/json">'
            '{"sku":"127074","availability":["Coming soon"],"isSalableQty":true,'
            '"prices({\\"personalized\\":false})":{"finalPrice":99.99,"regularPrice":99.99}}'
            "</script>"
            "Add to cart $99.99"
        )
        listing = Listing(
            "nintendo",
            "controller",
            "127074",
            "https://www.nintendo.com/us/store/products/x-127074/",
        )
        hit = from_page(listing, html, listing.url)
        self.assertFalse(hit.in_stock)
        self.assertEqual(hit.status, "COMING_SOON")
        self.assertEqual(hit.price, 99.99)

    def test_empty_page_is_error(self):
        hit = from_page(self.listing, "", self.listing.url, status=200)
        self.assertEqual(hit.status, "ERROR")

    def test_bestbuy_coming_soon_beats_jsonld_instock(self):
        html = (
            "<title>Switch 2 – The Legend of Zelda – 40th Anniversary Edition - Best Buy</title>"
            'sku 6691841 "customerPrice":519.99 '
            '"buttonStates":[{"buttonState":"COMING_SOON","condition":"NEW","displayText":"Coming Soon"}] '
            '"availability":"https://schema.org/InStock" Add to cart'
        )
        hit = from_page(
            Listing("bestbuy", "console", "6691841", "https://www.bestbuy.com/product/x/sku/6691841"),
            html,
            "https://www.bestbuy.com/product/x/sku/6691841",
        )
        self.assertFalse(hit.in_stock)
        self.assertEqual(hit.status, "COMING_SOON")
        self.assertEqual(hit.price, 519.99)

    def test_target_disabled_cart_is_sold_out_at_msrp(self):
        html = (
            "<title>Nintendo Switch 2 The Legend of Zelda 40th Anniversary Edition Console System : Target</title>"
            '<button class="styles_btn" type="button" disabled="">Add to cart</button>'
            "Free standard shipping with $35 orders."
        )
        hit = from_page(
            Listing("target", "console", "1013322047", "https://www.target.com/p/x/-/A-1013322047"),
            html,
            "https://www.target.com/p/x/-/A-1013322047",
        )
        self.assertFalse(hit.in_stock)
        self.assertEqual(hit.status, "SOLD_OUT")
        self.assertEqual(hit.price, 519.99)

    def test_shipping_threshold_is_not_product_price(self):
        html = (
            "<title>Nintendo Switch 2 The Legend of Zelda 40th Anniversary Edition Console System : Target</title>"
            "Free standard shipping with $35 orders. Currently unavailable"
        )
        hit = from_page(
            Listing("target", "console", "1013322047", "https://www.target.com/p/x/-/A-1013322047"),
            html,
            "https://www.target.com/p/x/-/A-1013322047",
        )
        self.assertNotEqual(hit.status, "WRONG_PRICE")
        self.assertNotEqual(hit.price, 35.0)


class TestAmazonPick(unittest.TestCase):
    def test_picks_matching_asin(self):
        html = (
            'data-asin="B0TEST0001"><img alt="PowerA Zelda Controller">'
            'data-asin="B0ZLDA40TH"><img alt="Nintendo Switch 2 The Legend of Zelda 40th Anniversary Edition">'
        )
        asin, title = pick_amazon_asin(html, CONSOLE)
        self.assertEqual(asin, "B0ZLDA40TH")
        self.assertIn("Zelda", title)

    def test_picks_h2_title_when_alt_missing(self):
        html = (
            'data-asin="B0ZLDA40TH"><div><h2>Nintendo Switch 2 The Legend of Zelda 40th Anniversary Edition</h2>'
        )
        asin, title = pick_amazon_asin(html, CONSOLE)
        self.assertEqual(asin, "B0ZLDA40TH")
        self.assertIn("40th", title)
