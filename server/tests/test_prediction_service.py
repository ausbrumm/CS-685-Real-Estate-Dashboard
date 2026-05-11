import datetime as dt
import math
import sys
import types
import unittest

np_stub = types.SimpleNamespace(
    random=types.SimpleNamespace(rand=lambda: 0.5),
    sqrt=math.sqrt,
)
sys.modules.setdefault("numpy", np_stub)

from infrastructure.prediction_service import PredictionService


def build_monthly_data(start_year: int = 2010, years: int = 8):
    data = []
    price = 100_000.0
    for year in range(start_year, start_year + years):
        for month in range(1, 13):
            last_day = 28 if month == 2 else 30 if month in {4, 6, 9, 11} else 31
            data.append((dt.date(year, month, last_day), price))
            price += 1_000.0 if month % 2 == 0 else -500.0
    return data


class PredictionServiceGroupSizeTests(unittest.TestCase):
    def setUp(self):
        self.service = PredictionService()
        self.data = build_monthly_data()

    def test_run_accepts_group_sizes_that_divide_twelve(self):
        for group_size in (1, 2, 3, 4, 6, 12):
            with self.subTest(group_size=group_size):
                results, *_ = self.service.run(self.data, group_size=group_size)
                self.assertIsInstance(results, list)

    def test_run_accepts_valid_k_values(self):
        for k in (1, 3, 5, 7, 9, 11):
            with self.subTest(k=k):
                results, *_ = self.service.run(self.data, k=k)
                self.assertIsInstance(results, list)

    def test_run_rejects_group_sizes_that_do_not_divide_twelve(self):
        for group_size in (0, 5, 7, 8, 10):
            with self.subTest(group_size=group_size):
                with self.assertRaisesRegex(
                    ValueError, "group_size must be a positive divisor of 12"
                ):
                    self.service.run(self.data, group_size=group_size)

    def test_run_rejects_invalid_k_values(self):
        for k in (-1, 0, 2, 4, 6, 8, 10, 12):
            with self.subTest(k=k):
                with self.assertRaisesRegex(
                    ValueError, "k must be an odd positive integer less than 12"
                ):
                    self.service.run(self.data, k=k)

    def test_group_size_six_uses_two_frequency_buckets(self):
        _, _, _, _, _, frequencies, _, _, _ = self.service.run(
            self.data, group_size=6
        )

        self.assertEqual(set(frequencies.keys()), {0, 1})

    def test_group_size_twelve_still_produces_predictions(self):
        results, *_ = self.service.run(self.data, group_size=12)

        self.assertTrue(any(result["predictions"] for result in results))


if __name__ == "__main__":
    unittest.main()
