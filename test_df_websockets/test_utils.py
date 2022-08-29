from unittest import TestCase

from df_websockets.utils import RE


class TestRE(TestCase):
    def test_re_valid(self):
        r = RE(r"^\d+")
        self.assertEqual("12", r("12"))

    def test_re_caster(self):
        r = RE(r"^\d+", caster=int)
        self.assertEqual(12, r("12"))

    def test_re_invalid(self):
        r = RE(r"^\d+", caster=int)
        self.assertRaises(ValueError, lambda: r("dqs"))
