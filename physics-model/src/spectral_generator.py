"""
Spectral time series generator for simulating sensor data streams
"""

import numpy as np
from typing import List, Dict, Any
from datetime import datetime, timedelta
try:
    from lspr_simulator import LSPRSimulator
except ImportError:
    from .lspr_simulator import LSPRSimulator


class SpectralGenerator:
    """
    Generates time series of spectral readings with realistic temporal patterns.
    """

    def __init__(
        self,
        simulator: LSPRSimulator,
        base_refractive_index: float = 1.33,
        contamination_rate: float = 0.0,
    ):
        """
        Initialize spectral generator.

        Args:
            simulator: LSPRSimulator instance
            base_refractive_index: Baseline refractive index
            contamination_rate: Rate of contamination increase (RIU/hour)
        """
        self.simulator = simulator
        self.base_n = base_refractive_index
        self.contamination_rate = contamination_rate

    def generate_refractive_index_series(
        self, duration_hours: float, interval_minutes: float = 5.0
    ) -> np.ndarray:
        """
        Generate time series of refractive index values.

        Args:
            duration_hours: Total duration (hours)
            interval_minutes: Sampling interval (minutes)

        Returns:
            Array of refractive index values
        """
        n_points = int(duration_hours * 60 / interval_minutes)
        time_hours = np.linspace(0, duration_hours, n_points)

        # Linear contamination trend
        contamination = self.contamination_rate * time_hours

        # Add diurnal variation (temperature effect)
        diurnal = 0.002 * np.sin(2 * np.pi * time_hours / 24)

        # Add random fluctuations
        noise = np.random.normal(0, 0.001, n_points)

        refractive_indices = self.base_n + contamination + diurnal + noise

        return refractive_indices

    def generate_reading(
        self, refractive_index: float, sensor_id: str, timestamp: datetime
    ) -> Dict[str, Any]:
        """
        Generate a single spectral reading.

        Args:
            refractive_index: Current refractive index
            sensor_id: Sensor identifier
            timestamp: Reading timestamp

        Returns:
            Dictionary with reading data
        """
        # Generate spectrum
        wavelengths, intensities = self.simulator.generate_spectrum(refractive_index)

        # Detect peak
        peak_wavelength = self.simulator.detect_peak_wavelength(wavelengths, intensities)

        # Calculate metrics
        delta_n = self.simulator.calculate_delta_n(peak_wavelength)
        risk_score = self.simulator.calculate_risk_score(delta_n)

        # Format intensities as comma-separated string
        intensities_str = ",".join([f"{val:.6f}" for val in intensities])

        return {
            "sensor_id": sensor_id,
            "timestamp": timestamp.isoformat(),
            "peak_wavelength": float(peak_wavelength),
            "intensities": intensities_str,
            "refractive_index": float(refractive_index),
            "delta_n": float(delta_n),
            "risk_score": float(risk_score),
        }

    def generate_time_series(
        self,
        sensor_id: str,
        start_time: datetime,
        duration_hours: float = 24.0,
        interval_minutes: float = 5.0,
    ) -> List[Dict[str, Any]]:
        """
        Generate complete time series of spectral readings.

        Args:
            sensor_id: Sensor identifier
            start_time: Start timestamp
            duration_hours: Total duration (hours)
            interval_minutes: Sampling interval (minutes)

        Returns:
            List of reading dictionaries
        """
        # Generate refractive index series
        n_series = self.generate_refractive_index_series(duration_hours, interval_minutes)

        # Generate readings
        readings = []
        interval_delta = timedelta(minutes=interval_minutes)

        for i, refractive_index in enumerate(n_series):
            timestamp = start_time + i * interval_delta
            reading = self.generate_reading(refractive_index, sensor_id, timestamp)
            readings.append(reading)

        return readings

    def generate_contamination_event(
        self,
        sensor_id: str,
        start_time: datetime,
        event_start_hour: float = 12.0,
        event_duration_hours: float = 6.0,
        contamination_magnitude: float = 0.05,
        total_duration_hours: float = 48.0,
        interval_minutes: float = 5.0,
    ) -> List[Dict[str, Any]]:
        """
        Generate time series with specific contamination event.

        Args:
            sensor_id: Sensor identifier
            start_time: Start timestamp
            event_start_hour: When contamination starts (hours from start)
            event_duration_hours: Duration of contamination buildup
            contamination_magnitude: Maximum Δn change
            total_duration_hours: Total simulation duration
            interval_minutes: Sampling interval

        Returns:
            List of reading dictionaries
        """
        n_points = int(total_duration_hours * 60 / interval_minutes)
        time_hours = np.linspace(0, total_duration_hours, n_points)

        # Create contamination profile (sigmoid)
        event_center = event_start_hour + event_duration_hours / 2
        steepness = 4.0 / event_duration_hours
        contamination = contamination_magnitude / (
            1 + np.exp(-steepness * (time_hours - event_center))
        )

        # Add background variation
        diurnal = 0.002 * np.sin(2 * np.pi * time_hours / 24)
        noise = np.random.normal(0, 0.001, n_points)

        n_series = self.base_n + contamination + diurnal + noise

        # Generate readings
        readings = []
        interval_delta = timedelta(minutes=interval_minutes)

        for i, refractive_index in enumerate(n_series):
            timestamp = start_time + i * interval_delta
            reading = self.generate_reading(refractive_index, sensor_id, timestamp)
            readings.append(reading)

        return readings
