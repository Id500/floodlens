import unittest
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from modules.risk_engine import calculate_flood_risk, _categorize_risk

class TestRiskEngine(unittest.TestCase):
    """Unit tests for the Explainable Flood Risk Engine."""

    def setUp(self):
        self.mock_weather = {
            "metrics": {
                "precip_24h_accum": 45.0,
                "precip_48h_accum": 80.0,
                "peak_hourly_intensity": 12.0,
                "total_7day_rainfall": 95.0
            },
            "current": {
                "temperature": 28.5,
                "humidity": 88
            },
            "daily_forecast": [
                {"precipitation_sum": 30.0},
                {"precipitation_sum": 25.0},
                {"precipitation_sum": 10.0}
            ]
        }

    def test_score_range_and_output_structure(self):
        """Ensure risk score remains strictly within [0, 100] with all expected keys."""
        mock_flood = {
            "has_river_data": True,
            "anomaly_ratio": 1.4,
            "current_discharge_m3s": 250.0,
            "historical_mean_m3s": 180.0
        }
        res = calculate_flood_risk(self.mock_weather, mock_flood)
        
        self.assertIn("risk_score", res)
        self.assertGreaterEqual(res["risk_score"], 0.0)
        self.assertLessEqual(res["risk_score"], 100.0)
        self.assertIn("classification", res)
        self.assertIn("contributing_factors", res)
        self.assertEqual(len(res["contributing_factors"]), 5)
        self.assertIn("explanation", res)
        self.assertIn("recommendations", res)
        self.assertTrue(len(res["recommendations"]) > 0)

    def test_severity_tier_categorization(self):
        """Verify score mapping to LOW, MODERATE, HIGH, SEVERE tiers."""
        self.assertEqual(_categorize_risk(12.0)[0], "LOW")
        self.assertEqual(_categorize_risk(35.0)[0], "MODERATE")
        self.assertEqual(_categorize_risk(62.0)[0], "HIGH")
        self.assertEqual(_categorize_risk(88.0)[0], "SEVERE")

    def test_dynamic_reweighting_when_river_data_missing(self):
        """Verify weights dynamically reallocate to 100% total when river data is absent."""
        mock_flood_absent = {
            "has_river_data": False,
            "anomaly_ratio": None,
            "current_discharge_m3s": None,
            "historical_mean_m3s": None
        }
        res = calculate_flood_risk(self.mock_weather, mock_flood_absent)
        
        weights = res["weights_applied"]
        self.assertEqual(sum(weights.values()), 100)
        self.assertEqual(weights["river_discharge"], 0)
        self.assertEqual(weights["precip_24h"], 35)
        self.assertEqual(weights["forecast_rain"], 35)
        self.assertEqual(weights["rain_intensity"], 20)
        self.assertEqual(weights["antecedent_saturation"], 10)
        self.assertIn("MODERATE", res["confidence"])

    def test_weighting_sum_with_river_data(self):
        """Verify weights sum to 100% when river data is present."""
        mock_flood_present = {
            "has_river_data": True,
            "anomaly_ratio": 2.2,
            "current_discharge_m3s": 500.0,
            "historical_mean_m3s": 220.0
        }
        res = calculate_flood_risk(self.mock_weather, mock_flood_present)
        weights = res["weights_applied"]
        self.assertEqual(sum(weights.values()), 100)
        self.assertEqual(weights["river_discharge"], 25)
        self.assertEqual(weights["precip_24h"], 25)
        self.assertEqual(weights["forecast_rain"], 25)
        self.assertEqual(weights["rain_intensity"], 15)
        self.assertEqual(weights["antecedent_saturation"], 10)
        self.assertIn("HIGH", res["confidence"])

    def test_extreme_weather_triggers_severe(self):
        """Extreme cloudburst and rainfall accumulation should trigger severe risk."""
        extreme_weather = {
            "metrics": {
                "precip_24h_accum": 220.0,
                "precip_48h_accum": 310.0,
                "peak_hourly_intensity": 45.0,
                "total_7day_rainfall": 280.0
            },
            "current": {"temperature": 24.0, "humidity": 98},
            "daily_forecast": [
                {"precipitation_sum": 120.0},
                {"precipitation_sum": 90.0},
                {"precipitation_sum": 60.0}
            ]
        }
        extreme_flood = {
            "has_river_data": True,
            "anomaly_ratio": 4.5,
            "current_discharge_m3s": 1200.0,
            "historical_mean_m3s": 250.0
        }
        res = calculate_flood_risk(extreme_weather, extreme_flood)
        self.assertGreaterEqual(res["risk_score"], 75.0)
        self.assertEqual(res["classification"], "SEVERE")

if __name__ == '__main__':
    unittest.main()

