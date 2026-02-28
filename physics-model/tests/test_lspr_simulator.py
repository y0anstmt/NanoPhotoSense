"""
Unit tests for LSPR simulator
"""

import pytest
import numpy as np
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from lspr_simulator import LSPRSimulator


class TestLSPRSimulator:
    """Test suite for LSPRSimulator"""

    def test_initialization(self):
        """Test simulator initialization with default parameters"""
        sim = LSPRSimulator()
        assert sim.particle_radius == 40.0
        assert sim.baseline_peak == 520.0
        assert sim.sensitivity == 60.0
        assert sim.baseline_n == 1.33

    def test_custom_initialization(self):
        """Test simulator initialization with custom parameters"""
        sim = LSPRSimulator(particle_radius=50.0, baseline_peak=530.0, sensitivity=70.0)
        assert sim.particle_radius == 50.0
        assert sim.baseline_peak == 530.0
        assert sim.sensitivity == 70.0

    def test_peak_shift_calculation(self):
        """Test peak wavelength shift calculation"""
        sim = LSPRSimulator(sensitivity=60.0)
        
        # No change
        shift = sim.calculate_peak_shift(1.33)
        assert shift == 0.0
        
        # Positive change
        shift = sim.calculate_peak_shift(1.34)
        assert pytest.approx(shift, abs=0.01) == 0.6
        
        # Negative change
        shift = sim.calculate_peak_shift(1.32)
        assert pytest.approx(shift, abs=0.01) == -0.6

    def test_spectrum_generation(self):
        """Test spectrum generation"""
        sim = LSPRSimulator()
        wavelengths, intensities = sim.generate_spectrum(1.33, noise_level=0.0)
        
        assert len(wavelengths) == len(intensities)
        assert len(wavelengths) == 300  # Default resolution
        assert wavelengths[0] == 400.0
        assert wavelengths[-1] == 700.0
        assert np.all(intensities >= 0)

    def test_peak_detection(self):
        """Test peak wavelength detection"""
        sim = LSPRSimulator(baseline_peak=520.0)
        wavelengths, intensities = sim.generate_spectrum(1.33, noise_level=0.0)
        
        peak = sim.detect_peak_wavelength(wavelengths, intensities)
        assert pytest.approx(peak, abs=5.0) == 520.0

    def test_delta_n_calculation(self):
        """Test refractive index change calculation"""
        sim = LSPRSimulator(baseline_peak=520.0, sensitivity=60.0)
        
        # Peak at 523 nm -> shift of 3 nm -> Δn = 0.05
        delta_n = sim.calculate_delta_n(523.0)
        assert pytest.approx(delta_n, abs=0.01) == 0.05

    def test_risk_score_calculation(self):
        """Test risk score calculation"""
        sim = LSPRSimulator()
        
        # Small change -> low risk
        risk = sim.calculate_risk_score(0.005)
        assert risk < 30
        
        # Moderate change -> moderate risk
        risk = sim.calculate_risk_score(0.015)
        assert 50 < risk < 80
        
        # Large change -> high risk
        risk = sim.calculate_risk_score(0.05)
        assert risk > 90
