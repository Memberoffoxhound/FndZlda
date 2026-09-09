import unittest

from fndzlda.catalog import CONSOLE, CONTROLLER
from fndzlda.identity import extract_price, matches_item, page_title


class TestMatch(unittest.TestCase):
    def test_console_title(self):
        t = "Nintendo Switch 2 \u2013 The Legend of Zelda \u2013 40th Anniversary Edition"
        self.assertTrue(matches_item(t, CONSOLE))
        self.assertFalse(matches_item(t, CONTROLLER))

    def test_controller_title(self):
        t = "Nintendo Switch 2 Pro Controller The Legend of Zelda 40th Anniversary Edition"
        self.assertTrue(matches_item(t, CONTROLLER))
        self.assertFalse(matches_item(t, CONSOLE))

    def test_reject_powera_and_oled_and_case(self):
        self.assertFalse(
            matches_item("PowerA Enhanced Wireless Controller Zelda 40th Switch 2", CONTROLLER)
        )
        self.assertFalse(
            matches_item("Nintendo Switch OLED Zelda Tears of the Kingdom Edition", CONSOLE)
        )
        self.assertFalse(
            matches_item("Switch 2 Zelda 40th Anniversary Carrying Case", CONSOLE)
        )

    def test_page_title(self):
        html = "<html><head><title>Switch 2 \u2013 The Legend of Zelda \u2013 40th Anniversary Edition : Target</title></head>"
        self.assertIn("Zelda", page_title(html))

    def test_price(self):
        self.assertEqual(extract_price("MSRP $519.99 ships free"), 519.99)
        self.assertEqual(extract_price("Current price is $99.00"), 99.00)
