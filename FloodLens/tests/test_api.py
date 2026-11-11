import unittest
from unittest.mock import patch, MagicMock
import sys
import io
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app
from models import db
from models.report import FloodReport

class TestFlaskEndpoints(unittest.TestCase):
    """Integration test suite for Flask application routes and REST APIs."""

    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config['TESTING'] = True
        cls.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        cls.client = cls.app.test_client()

        with cls.app.app_context():
            db.create_all()

    def test_page_routes_status_200(self):
        """Verify all 9 frontend dashboard pages return HTTP 200 OK."""
        routes = [
            '/',
            '/weather',
            '/satellite',
            '/risk',
            '/river',
            '/analysis',
            '/map',
            '/reports',
            '/about'
        ]
        for route in routes:
            with self.subTest(route=route):
                response = self.client.get(route)
                self.assertEqual(response.status_code, 200, f"Route {route} failed to load.")

    def test_api_satellite_metadata(self):
        """Verify NASA GIBS satellite metadata endpoint."""
        res = self.client.get('/api/satellite')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertIn('layers', data['data'])
        self.assertIn('tile_url', data['data'])

    def test_api_presets(self):
        """Verify location presets endpoint."""
        res = self.client.get('/api/presets')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertTrue(len(data['presets']) >= 5)

    def test_api_weather_validation_error(self):
        """Verify coordinate validation on /api/weather rejects invalid latitudes."""
        res_bad = self.client.get('/api/weather?lat=999&lon=999')
        self.assertEqual(res_bad.status_code, 400)
        self.assertFalse(res_bad.get_json()['success'])

    @patch('modules.weather.requests.get')
    def test_api_weather_success(self, mock_get):
        """Verify /api/weather endpoint processes Open-Meteo responses cleanly."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "latitude": 13.0827,
            "longitude": 80.2707,
            "timezone": "Asia/Kolkata",
            "current": {
                "temperature_2m": 31.2,
                "apparent_temperature": 36.5,
                "relative_humidity_2m": 78,
                "precipitation": 2.5,
                "rain": 2.5,
                "weather_code": 63,
                "surface_pressure": 1008.5,
                "wind_speed_10m": 16.2,
                "wind_direction_10m": 85,
                "wind_gusts_10m": 24.1,
                "is_day": 1
            },
            "hourly": {
                "time": [f"2026-11-09T{i:02d}:00" for i in range(24)],
                "temperature_2m": [30.0 + (i % 3) for i in range(24)],
                "relative_humidity_2m": [75 for _ in range(24)],
                "precipitation_probability": [40 for _ in range(24)],
                "precipitation": [1.5 for _ in range(24)],
                "rain": [1.5 for _ in range(24)],
                "weather_code": [61 for _ in range(24)],
                "wind_speed_10m": [14.0 for _ in range(24)]
            },
            "daily": {
                "time": [f"2026-11-{9+i:02d}" for i in range(7)],
                "weather_code": [63 for _ in range(7)],
                "temperature_2m_max": [32.0 for _ in range(7)],
                "temperature_2m_min": [25.0 for _ in range(7)],
                "precipitation_sum": [15.0 for _ in range(7)],
                "precipitation_hours": [4.0 for _ in range(7)],
                "precipitation_probability_max": [70 for _ in range(7)],
                "wind_speed_10m_max": [22.0 for _ in range(7)]
            }
        }
        mock_get.return_value = mock_resp

        res = self.client.get('/api/weather?lat=13.0827&lon=80.2707')
        self.assertEqual(res.status_code, 200)
        json_data = res.get_json()
        self.assertTrue(json_data['success'])
        self.assertIn('metrics', json_data['data'])
        self.assertEqual(json_data['data']['current']['temperature'], 31.2)
        self.assertAlmostEqual(json_data['data']['metrics']['precip_24h_accum'], 36.0, delta=0.5)

    @patch('modules.flood_api.requests.get')
    def test_api_flood_endpoint(self, mock_get):
        """Verify /api/flood endpoint returns valid GloFAS structure."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "latitude": 13.0827,
            "longitude": 80.2707,
            "daily": {
                "time": [f"2026-11-{2+i:02d}" for i in range(14)],
                "river_discharge": [45.0 + i for i in range(14)],
                "river_discharge_mean": [35.0 for _ in range(14)],
                "river_discharge_median": [32.0 for _ in range(14)],
                "river_discharge_max": [60.0 for _ in range(14)],
                "river_discharge_min": [20.0 for _ in range(14)]
            }
        }
        mock_get.return_value = mock_resp

        res = self.client.get('/api/flood?lat=13.0827&lon=80.2707')
        self.assertEqual(res.status_code, 200)
        json_data = res.get_json()
        self.assertTrue(json_data['success'])
        self.assertTrue(json_data['data']['has_river_data'])
        self.assertGreater(json_data['data']['current_discharge_m3s'], 0)

    @patch('app.fetch_river_discharge')
    @patch('app.fetch_weather_data')
    def test_api_risk_scoring(self, mock_weather, mock_flood):
        """Verify multi-factor risk score calculation endpoint."""
        mock_weather.return_value = {
            "metrics": {
                "precip_24h_accum": 50.0,
                "precip_48h_accum": 90.0,
                "peak_hourly_intensity": 15.0,
                "total_7day_rainfall": 110.0
            },
            "current": {"temperature": 29.0, "humidity": 85},
            "daily_forecast": [
                {"precipitation_sum": 35.0},
                {"precipitation_sum": 30.0},
                {"precipitation_sum": 20.0}
            ]
        }
        mock_flood.return_value = {
            "has_river_data": True,
            "anomaly_ratio": 1.6,
            "current_discharge_m3s": 320.0,
            "historical_mean_m3s": 200.0
        }

        res = self.client.get('/api/risk?lat=13.0827&lon=80.2707')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        risk = data['data']
        self.assertGreaterEqual(risk['risk_score'], 0.0)
        self.assertLessEqual(risk['risk_score'], 100.0)
        self.assertIn(risk['classification'], ['LOW', 'MODERATE', 'HIGH', 'SEVERE'])
        self.assertEqual(len(risk['contributing_factors']), 5)

    def test_community_reports_crud(self):
        """Test community report submission (POST) and retrieval (GET)."""
        # GET existing reports
        res_get = self.client.get('/api/reports')
        self.assertEqual(res_get.status_code, 200)

        # POST new valid report
        payload = {
            'location_name': 'Velachery 100ft Test Road',
            'latitude': 12.9815,
            'longitude': 80.2180,
            'severity': 'Severe',
            'water_depth': 'Knee deep (15-50cm)',
            'description': 'Test automated waterlogging entry for unit test.',
            'reporter_name': 'Test Runner'
        }
        res_post = self.client.post('/api/reports', data=payload)
        self.assertEqual(res_post.status_code, 201)
        post_data = res_post.get_json()
        self.assertTrue(post_data['success'])
        self.assertEqual(post_data['report']['status'], 'Unverified')

    def test_image_analysis_endpoint(self):
        """Test OpenCV satellite image upload and segmentation analysis."""
        sample_path = Path(__file__).resolve().parent.parent / 'uploads' / 'sample_satellite.jpg'
        if not sample_path.exists():
            self.skipTest("Sample image not found on disk")

        with open(sample_path, 'rb') as img_f:
            img_bytes = img_f.read()

        data = {
            'image': (io.BytesIO(img_bytes), 'test_satellite.jpg')
        }

        res = self.client.post('/api/analyze-image', data=data, content_type='multipart/form-data')
        self.assertEqual(res.status_code, 200)
        res_json = res.get_json()
        self.assertTrue(res_json['success'])
        self.assertIn('water_detection', res_json)
        self.assertIn('quality_diagnostics', res_json)
        self.assertGreater(res_json['water_detection']['water_coverage_percentage'], 0.0)

if __name__ == '__main__':
    unittest.main()
