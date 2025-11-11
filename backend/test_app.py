#!/usr/bin/env python3
"""
Unit tests for the backend API
"""
import unittest
import json
import os
import tempfile
from datetime import datetime, timedelta
from app import app, init_db, store_telemetry, get_recent_telemetry, DB_PATH


class TestBackendAPI(unittest.TestCase):
    """Test cases for backend API endpoints"""

    @classmethod
    def setUpClass(cls):
        """Set up test database"""
        cls.test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        cls.test_db_path = cls.test_db.name
        cls.test_db.close()

    @classmethod
    def tearDownClass(cls):
        """Clean up test database"""
        if os.path.exists(cls.test_db_path):
            os.unlink(cls.test_db_path)

    def setUp(self):
        """Set up test client and database"""
        # Monkey patch DB_PATH for testing
        import app as app_module
        self.original_db_path = app_module.DB_PATH
        app_module.DB_PATH = self.test_db_path

        # Initialize test database
        init_db()

        # Create test client
        app.config['TESTING'] = True
        self.client = app.test_client()

    def tearDown(self):
        """Restore original DB_PATH"""
        import app as app_module
        app_module.DB_PATH = self.original_db_path

    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')

    def test_receive_telemetry(self):
        """Test receiving telemetry data"""
        payload = {
            "timestamp": datetime.utcnow().isoformat(),
            "signals": {
                "sine_wave": 5.5,
                "cosine_wave": 3.2,
                "random_noise": 1.8
            }
        }

        response = self.client.post(
            '/api/telemetry',
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')

    def test_receive_telemetry_invalid_payload(self):
        """Test receiving invalid telemetry data"""
        # Missing timestamp
        payload = {
            "signals": {
                "sine_wave": 5.5
            }
        }

        response = self.client.post(
            '/api/telemetry',
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)

    def test_get_telemetry(self):
        """Test retrieving telemetry data"""
        # Store some test data
        timestamp = datetime.utcnow().isoformat()
        signals = {
            "sine_wave": 5.5,
            "cosine_wave": 3.2
        }

        import app as app_module
        store_telemetry(timestamp, signals)

        # Retrieve data
        response = self.client.get('/api/telemetry?hours=1')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertIn('sine_wave', data)
        self.assertIn('cosine_wave', data)
        self.assertEqual(len(data['sine_wave']), 1)
        self.assertEqual(data['sine_wave'][0]['value'], 5.5)

    def test_get_signals(self):
        """Test retrieving list of signals"""
        # Store some test data
        timestamp = datetime.utcnow().isoformat()
        signals = {
            "sine_wave": 5.5,
            "cosine_wave": 3.2,
            "random_noise": 1.8
        }

        import app as app_module
        store_telemetry(timestamp, signals)

        # Retrieve signals list
        response = self.client.get('/api/signals')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertIsInstance(data, list)
        self.assertIn('sine_wave', data)
        self.assertIn('cosine_wave', data)
        self.assertIn('random_noise', data)

    def test_get_recent_telemetry_filtering(self):
        """Test that get_recent_telemetry filters by time correctly"""
        import app as app_module

        # Store old data (2 hours ago)
        old_timestamp = (datetime.utcnow() - timedelta(hours=2)).isoformat()
        store_telemetry(old_timestamp, {"old_signal": 1.0})

        # Store recent data
        recent_timestamp = datetime.utcnow().isoformat()
        store_telemetry(recent_timestamp, {"new_signal": 2.0})

        # Get data from last 1 hour
        data = get_recent_telemetry(hours=1)

        # Should only contain new_signal
        self.assertIn('new_signal', data)
        self.assertNotIn('old_signal', data)


class TestSignalGeneration(unittest.TestCase):
    """Test cases for signal generation (producer)"""

    def test_multiple_signals_received(self):
        """Test that multiple signal types are properly handled"""
        app.config['TESTING'] = True
        client = app.test_client()

        # Create temporary test database
        test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        test_db_path = test_db.name
        test_db.close()

        # Monkey patch DB_PATH
        import app as app_module
        original_db_path = app_module.DB_PATH
        app_module.DB_PATH = test_db_path

        try:
            init_db()

            # Send multiple data points
            for i in range(5):
                payload = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "signals": {
                        "sine_wave": float(i),
                        "cosine_wave": float(i * 2)
                    }
                }

                response = client.post(
                    '/api/telemetry',
                    data=json.dumps(payload),
                    content_type='application/json'
                )
                self.assertEqual(response.status_code, 200)

            # Verify all data was stored
            response = client.get('/api/telemetry?hours=1')
            data = json.loads(response.data)

            self.assertEqual(len(data['sine_wave']), 5)
            self.assertEqual(len(data['cosine_wave']), 5)

        finally:
            # Cleanup
            app_module.DB_PATH = original_db_path
            if os.path.exists(test_db_path):
                os.unlink(test_db_path)


if __name__ == '__main__':
    unittest.main()
