import unittest

from fndzlda.catalog import parse_shops


class TestParseShops(unittest.TestCase):
    def test_all(self):
        shops, unknown = parse_shops("all")
        self.assertEqual(shops, {"nintendo", "bestbuy", "target", "walmart", "gamestop", "amazon"})
        self.assertEqual(unknown, [])

    def test_comma_list(self):
        shops, unknown = parse_shops("walmart, target")
        self.assertEqual(shops, {"walmart", "target"})
        self.assertEqual(unknown, [])

    def test_typos(self):
        shops, unknown = parse_shops("best byu, gamestp, amazom, targt")
        self.assertEqual(unknown, [])
        self.assertEqual(shops, {"bestbuy", "gamestop", "amazon", "target"})

    def test_short_codes(self):
        shops, unknown = parse_shops("bb, wmt, gs, amzn")
        self.assertEqual(unknown, [])
        self.assertEqual(shops, {"bestbuy", "walmart", "gamestop", "amazon"})

    def test_unknown_kept(self):
        shops, unknown = parse_shops("walmart, costco")
        self.assertEqual(shops, {"walmart"})
        self.assertEqual(unknown, ["costco"])
