"""Regression tests for the normalization engine.

Pure-function coverage (no DB, no models): Indian number formats, unit
normalization, fiscal-year handling, attribute classification and
plausibility bands. Run with: python3 -m unittest discover -s tests
"""

import unittest

from backend.core.normalize import (
    clean_text,
    context_unit,
    detect_attribute,
    fy_label,
    in_range,
    normalize_period,
    parse_number,
    parse_quantity,
)


class ParseNumberTest(unittest.TestCase):
    def test_indian_grouping(self):
        self.assertAlmostEqual(parse_number("1,23,456.78"), 123456.78)

    def test_plain(self):
        self.assertAlmostEqual(parse_number("48.5"), 48.5)

    def test_none_when_absent(self):
        self.assertIsNone(parse_number("no digits here"))


class ParseQuantityTest(unittest.TestCase):
    def test_lakh_tonnes(self):
        self.assertEqual(parse_quantity("12.5 lakh tonnes"), (1250000.0, "tonnes"))

    def test_million_tonnes(self):
        self.assertEqual(parse_quantity("3.2 MT"), (3200000.0, "tonnes"))

    def test_crore(self):
        self.assertEqual(parse_quantity("2.5 crore"), (25000000.0, None))

    def test_percent(self):
        self.assertEqual(parse_quantity("34.2 %"), (34.2, "percent"))

    def test_gcv(self):
        self.assertEqual(parse_quantity("5,800 kcal/kg"), (5800.0, "kcal/kg"))

    def test_bare_number_has_no_unit(self):
        self.assertEqual(parse_quantity("48.5"), (48.5, None))


class NormalizePeriodTest(unittest.TestCase):
    def test_fy_span(self):
        self.assertEqual(normalize_period("2021-22"), "2021-04-01")

    def test_fy_prefix(self):
        self.assertEqual(normalize_period("FY22"), "2021-04-01")

    def test_bare_year_is_calendar(self):
        self.assertEqual(normalize_period("2021"), "2021-01-01")

    def test_march_position_belongs_to_fy(self):
        self.assertEqual(normalize_period("as on 31st March 2022"), "2021-04-01")

    def test_unknown(self):
        self.assertIsNone(normalize_period("sometime later"))


class FyLabelTest(unittest.TestCase):
    def test_fy(self):
        self.assertEqual(fy_label("2021-04-01"), "FY2021-22")

    def test_calendar(self):
        self.assertEqual(fy_label("2021-01-01"), "2021")

    def test_missing(self):
        self.assertEqual(fy_label(None), "-")


class ContextUnitTest(unittest.TestCase):
    def test_header_unit(self):
        self.assertEqual(context_unit("Production (lakh tonnes)"), ("tonnes", 1e5))

    def test_no_unit(self):
        self.assertEqual(context_unit("Mine name"), (None, 1.0))


class AttributeTest(unittest.TestCase):
    def test_nearest_keyword_wins(self):
        attr = detect_attribute("reserves of 412 MT with GCV of ")
        self.assertEqual(attr, "gcv")

    def test_unknown(self):
        self.assertIsNone(detect_attribute("the quick brown fox"))


class InRangeTest(unittest.TestCase):
    def test_ash_band(self):
        self.assertTrue(in_range("ash_pct", 34.0))
        self.assertFalse(in_range("ash_pct", 140.0))

    def test_gcv_band(self):
        self.assertTrue(in_range("gcv", 5800.0))
        self.assertFalse(in_range("gcv", 50.0))

    def test_unknown_attribute_passes(self):
        self.assertTrue(in_range("production", 1e9))


class CleanTextTest(unittest.TestCase):
    def test_dehyphenates_line_breaks(self):
        self.assertEqual(clean_text("produc-\ntion"), "production")

    def test_strips_soft_hyphen(self):
        self.assertEqual(clean_text("produc­tion"), "production")

    def test_collapses_spaces(self):
        self.assertEqual(clean_text("a   b"), "a b")


if __name__ == "__main__":
    unittest.main()
