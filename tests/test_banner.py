import unittest

from fndzlda.banner import render


class TestBanner(unittest.TestCase):
    def test_ocarina_wordmark(self):
        art = render(color=False, unicode=True)
        self.assertIn("O C A R I N A", art)
        self.assertIn("L E G E N D", art)
        self.assertIn("FndZlda", art)
        self.assertIn("1998", art)
        self.assertIn("/\\", art)
        self.assertIn("/______\\", art)

    def test_ascii_fallback(self):
        art = render(color=False, unicode=False)
        self.assertIn("O C A R I N A", art)
        self.assertIn("ZZZZZ", art)
        self.assertIn("1998", art)

    def test_color_codes_when_asked(self):
        art = render(color=True, unicode=True)
        self.assertIn("\033[", art)
        self.assertIn("O C A R I N A", art)
