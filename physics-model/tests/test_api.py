"""
API endpoint tests
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from api import app

client = TestClient(app)


class TestAPI:
    """Test suite for FastAPI endpoints"""

    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    def test_generate_spectrum(self):
        """Test spectrum generation endpoint"""
        request_data = {"refractive_index": 1.34, "noise_level": 0.02}

        response = client.post("/api/spectrum", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert "wavelengths" in data
        assert "intensities" in data
        assert "peak_wavelength" in data
        assert "delta_n" in data
        assert "risk_score" in data
        assert len(data["wavelengths"]) == len(data["intensities"])

    def test_generate_time_series(self):
        """Test time series generation endpoint"""
        request_data = {
            "sensor_id": "TEST-001",
            "duration_hours": 1.0,
            "interval_minutes": 10.0,
            "contamination_rate": 0.001,
        }

        response = client.post("/api/timeseries", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert "readings" in data
        assert "count" in data
        assert "summary" in data
        assert data["count"] > 0
        assert len(data["readings"]) == data["count"]

    def test_generate_contamination_event(self):
        """Test contamination event endpoint"""
        request_data = {
            "sensor_id": "TEST-001",
            "event_start_hour": 0.5,
            "event_duration_hours": 1.0,
            "contamination_magnitude": 0.03,
            "total_duration_hours": 2.0,
            "interval_minutes": 10.0,
        }

        response = client.post("/api/contamination-event", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert "readings" in data
        assert data["count"] > 0

        # Verify risk increases during event
        risk_scores = [r["risk_score"] for r in data["readings"]]
        max_risk = max(risk_scores)
        assert max_risk > 50  # Should see elevated risk

    def test_invalid_refractive_index(self):
        """Test validation for invalid refractive index"""
        request_data = {"refractive_index": 3.0, "noise_level": 0.02}

        response = client.post("/api/spectrum", json=request_data)
        assert response.status_code == 422  # Validation error
