import unittest

from fndzlda.banner import disappointment, hey_listen, render, render_intro, render_ocarina


class TestBanner(unittest.TestCase):
    def test_ascii_crest_and_subtitle(self):
        art = render(color=False, unicode=True)
        self.assertNotIn("▀", art)
        self.assertNotIn("▄", art)
        self.assertIn("@@@@@@@@@@@@@@@@@@@@@@@@@@@@", art)
        self.assertIn("OCARINA", art.replace(" ", ""))
        self.assertIn("FndZlda", art)

    def test_ascii_fallback(self):
        art = render(color=False, unicode=False)
        self.assertNotIn("▀", art)
        self.assertIn("@@@@@@@@@@@@@@@@@@@@@@@@@@@@", art)
        self.assertIn("OCARINA", art.replace(" ", ""))
        self.assertIn("FndZlda", art)

    def test_color_codes_when_asked(self):
        art = render(color=True, unicode=True)
        self.assertIn("\033[38;5;", art)
        self.assertNotIn("\033[38;2;", art)
        self.assertIn("OCARINA", art.replace(" ", ""))

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

    def test_ocarina_subtitle(self):
        art = render_ocarina(color=False)
        self.assertIn("O C A R I N A", art)
        gold = render_ocarina(color=True)
        self.assertIn("\033[", gold)
        self.assertIn("O C A R I N A", gold)
