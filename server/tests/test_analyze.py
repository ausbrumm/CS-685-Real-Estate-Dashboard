import datetime as dt
import math
import sys
import types
import unittest

np_stub = types.SimpleNamespace(sqrt=math.sqrt)
sys.modules.setdefault("numpy", np_stub)

postgres_stub = types.ModuleType("infrastructure.postgres_connector")
postgres_stub.AsyncPostgresConnector = object
sys.modules.setdefault("infrastructure.postgres_connector", postgres_stub)

prediction_stub = types.ModuleType("infrastructure.prediction_service")
prediction_stub.PredictionService = object
sys.modules.setdefault("infrastructure.prediction_service", prediction_stub)

from analyze import (
    _build_accuracy_stats,
    _build_future_summary,
    _calculate_bound_accuracy,
    _format_report,
    _next_month_date,
    _resolve_log_target,
)


class AnalyzeHelpersTests(unittest.TestCase):
    def test_next_month_date_advances_to_month_end(self):
        self.assertEqual(_next_month_date(dt.date(2024, 4, 30)), dt.date(2024, 5, 31))
        self.assertEqual(_next_month_date(dt.date(2024, 12, 31)), dt.date(2025, 1, 31))

    def test_build_future_summary_uses_last_actual_and_next_prediction(self):
        summary = _build_future_summary(
            region_id=394463,
            region_name="Example Region",
            group_size=3,
            k=5,
            projected_data=[
                (dt.date(2024, 12, 31), 100_000.0),
                (dt.date(2025, 1, 31), 103_500.0),
            ],
            prediction_accuracy=0.72,
            bounds_accuracy=0.64,
        )

        self.assertEqual(summary["region"], 394463)
        self.assertEqual(summary["group_size"], 3)
        self.assertEqual(summary["k"], 5)
        self.assertEqual(summary["direction"], "U")
        self.assertEqual(summary["change"], 3_500.0)
        self.assertAlmostEqual(summary["pct_change"], 0.035)
        self.assertAlmostEqual(summary["prediction_accuracy"], 0.72)
        self.assertAlmostEqual(summary["bounds_accuracy"], 0.64)

    def test_format_report_includes_accuracy_columns(self):
        report = _format_report(
            [
                {
                    "region": 394463,
                    "region_name": "Example Region",
                    "group_size": 4,
                    "k": 7,
                    "last_date": dt.date(2024, 12, 31),
                    "predicted_date": dt.date(2025, 1, 31),
                    "last_price": 100_000.0,
                    "predicted_price": 99_000.0,
                    "change": -1_000.0,
                    "pct_change": -0.01,
                    "direction": "D",
                    "prediction_accuracy": 0.78,
                    "bounds_accuracy": 0.56,
                }
            ]
        )

        self.assertIn("Group Size", report)
        self.assertIn("Pred Acc", report)
        self.assertIn("Bound Acc", report)
        self.assertIn("394463", report)
        self.assertIn("Example Region", report)
        self.assertIn("4", report)
        self.assertIn("7", report)
        self.assertIn("78.00%", report)
        self.assertIn("56.00%", report)

    def test_calculate_bound_accuracy_uses_actual_dates_within_bounds(self):
        actual_data = [
            (dt.date(2024, 1, 31), 100.0),
            (dt.date(2024, 2, 29), 108.0),
            (dt.date(2024, 3, 31), 91.0),
        ]
        error_band = [
            {
                "date": dt.date(2024, 1, 31),
                "predicted": 100.0,
                "lower": 98.0,
                "upper": 102.0,
            },
            {
                "date": dt.date(2024, 2, 29),
                "predicted": 103.0,
                "lower": 100.0,
                "upper": 107.0,
            },
            {
                "date": dt.date(2024, 3, 31),
                "predicted": 95.0,
                "lower": 90.0,
                "upper": 96.0,
            },
        ]

        self.assertAlmostEqual(
            _calculate_bound_accuracy(actual_data, error_band),
            2 / 3,
        )

    def test_build_accuracy_stats_averages_prediction_and_bounds_accuracy(self):
        runs = [
            (
                [],
                {},
                {},
                {},
                [(dt.date(2024, 1, 31), 100.0)],
                {},
                {"accuracy": 0.6},
                [
                    {
                        "date": dt.date(2024, 1, 31),
                        "predicted": 100.0,
                        "lower": 99.0,
                        "upper": 101.0,
                    }
                ],
                None,
            ),
            (
                [],
                {},
                {},
                {},
                [(dt.date(2024, 1, 31), 103.0)],
                {},
                {"accuracy": 0.8},
                [
                    {
                        "date": dt.date(2024, 1, 31),
                        "predicted": 100.0,
                        "lower": 99.0,
                        "upper": 101.0,
                    }
                ],
                None,
            ),
        ]

        class FakePredictionService:
            def __init__(self, run_results):
                self._run_results = iter(run_results)

            def run(self, *args, **kwargs):
                return next(self._run_results)

        stats = _build_accuracy_stats(
            FakePredictionService(runs),
            data=[(dt.date(2024, 1, 31), 100.0)],
            group_size=3,
            k=5,
            runs=2,
        )

        self.assertAlmostEqual(stats["prediction_accuracy"], 0.7)
        self.assertAlmostEqual(stats["bounds_accuracy"], 0.5)

    def test_resolve_log_target_uses_single_file_per_region(self):
        log_path, mode = _resolve_log_target([394463], group_size=3, k=5)
        self.assertEqual(log_path, "logs/region_394463.txt")
        self.assertEqual(mode, "a")

    def test_resolve_log_target_keeps_multi_region_file_naming(self):
        log_path, mode = _resolve_log_target([394463, 394910], group_size=3, k=5)
        self.assertEqual(log_path, "logs/g3_k5.txt")
        self.assertEqual(mode, "w")


if __name__ == "__main__":
    unittest.main()
