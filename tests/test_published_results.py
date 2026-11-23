import csv
import unittest
from pathlib import Path
from statistics import mean


ROOT = Path(__file__).resolve().parents[1]


def read_rows(path):
    with (ROOT / path).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


class PublishedResultsTest(unittest.TestCase):
    def test_scores_match_chronological_predictions(self):
        history = read_rows("data/processed/national_ewaste_full.csv")
        self.assertEqual([int(row["year_index"]) for row in history],
                         list(range(1, len(history) + 1)))
        predictions = read_rows("outputs/model_results/model_predictions.csv")
        metrics = read_rows("outputs/model_results/model_metrics.csv")
        self.assertEqual(len({row["Model"] for row in metrics}), 7)
        self.assertEqual({row["Model"] for row in metrics},
                         {row["model"] for row in predictions})
        for score in metrics:
            with self.subTest(model=score["Model"]):
                folds = [row for row in predictions if row["model"] == score["Model"]]
                self.assertEqual(sorted(int(row["train_size"]) for row in folds),
                                 list(range(4, len(history))))
                errors = []
                for fold in folds:
                    target = history[int(fold["train_size"])]
                    self.assertEqual(fold["test_fy"], target["financial_year"])
                    actual = float(target["ewaste_generated_tonnes"])
                    self.assertAlmostEqual(float(fold["actual"]), actual)
                    errors.append(abs(float(fold["predicted"]) - actual))
                self.assertAlmostEqual(float(score["MAE_tonnes"]), mean(errors), delta=0.5)

    def test_power_bi_uses_published_model_results(self):
        for name in ("model_metrics.csv", "model_predictions.csv",
                     "model_robustness_results.csv", "forecast_results.csv"):
            with self.subTest(file=name):
                self.assertEqual(read_rows("outputs/model_results/" + name),
                                 read_rows("outputs/power_bi/" + name))


class ForecastSanityTest(unittest.TestCase):
    """Guards for the issues found in review: impossible forecasts, silent fallbacks, overclaimed ranking."""

    def test_gp_intervals_are_positive_and_ordered(self):
        gp = [r for r in read_rows("outputs/model_results/forecast_results.csv")
              if r["model"] == "Gaussian Process"]
        self.assertEqual(len(gp), 6)
        for row in gp:
            low, mid, high = (float(row["gp_95ci_low"]), float(row["forecast_tonnes"]),
                              float(row["gp_95ci_high"]))
            self.assertGreater(low, 0, "e-waste tonnage cannot be negative")
            self.assertLess(low, mid)
            self.assertLess(mid, high)

    def test_all_forecasts_are_positive(self):
        for row in read_rows("outputs/model_results/forecast_results.csv"):
            self.assertGreater(float(row["forecast_tonnes"]), 0)

    def test_scenario_band_is_ordered_and_excludes_trees(self):
        rows = read_rows("outputs/model_results/scenario_band.csv")
        self.assertEqual(len(rows), 6)
        for row in rows:
            self.assertLessEqual(float(row["low_tonnes"]), float(row["base_tonnes"]))
            self.assertLessEqual(float(row["base_tonnes"]), float(row["high_tonnes"]))
            self.assertNotIn("Random Forest", row["models_in_band"])
            self.assertNotIn("XGBoost", row["models_in_band"])

    def test_framework_flag_identified_only_in_last_fold(self):
        rows = read_rows("outputs/model_results/framework_flag_diagnostic.csv")
        identified = [r["train_size"] for r in rows if r["flag_identified"] == "True"]
        self.assertEqual(identified, ["7"])

    def test_fold_sensitivity_reports_rank_span_for_every_model(self):
        rows = read_rows("outputs/model_results/fold_sensitivity.csv")
        self.assertEqual(len(rows), 7)
        for row in rows:
            self.assertLessEqual(int(row["best_rank"]), int(row["worst_rank"]))

    def test_arima_diagnostics_file_exists(self):
        # Fallbacks/convergence problems must be recorded, never silent.
        self.assertTrue((ROOT / "outputs/model_results/arima_diagnostics.csv").exists())
