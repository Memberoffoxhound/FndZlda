import unittest

from fndzlda.banner import disappointment, hey_listen, render, render_intro


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

    def test_cave_and_master_sword_intro(self):
        art = render_intro(color=False)
        self.assertIn("IT'S DANGEROUS TO GO ALONE!", art)
        self.assertIn("TAKE THIS!", art)
        self.assertIn("MASTER SWORD", art)

    def test_disappointment_is_zelda(self):
        text = disappointment(1, color=False)
        self.assertIn("terrible fate", text)
        self.assertIn("Majora", text)
        text2 = disappointment(2, color=False)
        self.assertIn("richer", text2)

    def test_hit_is_navi(self):
        text = hey_listen(color=False)
        self.assertIn("HEY! LISTEN!!!", text)
