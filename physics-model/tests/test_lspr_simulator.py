"""
Unit tests for LSPR simulator
"""

import pytest
import numpy as np
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from lspr_simulator import (
    LSPRSimulator,
    compute_lspr_spectrum,
    apply_refractive_index_shift,
    generate_temporal_series,
    slow_infiltration_profile,
    fast_infiltration_profile,
    add_gaussian_noise,
    create_infiltration_profile
)


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


class TestStandaloneLSPRFunctions:
    """Test suite for standalone LSPR modeling functions"""

    def test_compute_lspr_spectrum(self):
        """Test Gaussian LSPR spectrum generation"""
        wavelengths = np.linspace(400, 700, 300)
        peak_center = 520.0
        peak_width = 40.0
        amplitude = 1.0
        
        intensities = compute_lspr_spectrum(wavelengths, peak_center, peak_width, amplitude)
        
        # Check output shape
        assert len(intensities) == len(wavelengths)
        
        # Check peak is at center
        peak_idx = np.argmax(intensities)
        assert pytest.approx(wavelengths[peak_idx], abs=2.0) == peak_center
        
        # Check peak amplitude
        assert pytest.approx(intensities[peak_idx], abs=0.01) == amplitude
        
        # Check Gaussian shape (values decrease away from peak)
        assert intensities[peak_idx - 20] < intensities[peak_idx]
        assert intensities[peak_idx + 20] < intensities[peak_idx]
        
        # Check all values are positive
        assert np.all(intensities >= 0)
    
    def test_apply_refractive_index_shift(self):
        """Test refractive index shift calculation"""
        base_peak = 520.0
        delta_n = 0.01
        sensitivity_k = 200.0
        
        shifted_peak = apply_refractive_index_shift(base_peak, delta_n, sensitivity_k)
        
        # Expected shift: Δλ = k × Δn = 200 × 0.01 = 2.0 nm
        expected_peak = base_peak + 2.0
        assert pytest.approx(shifted_peak, abs=0.01) == expected_peak
    
    def test_apply_refractive_index_shift_negative(self):
        """Test refractive index shift with negative delta_n"""
        base_peak = 520.0
        delta_n = -0.005
        sensitivity_k = 200.0
        
        shifted_peak = apply_refractive_index_shift(base_peak, delta_n, sensitivity_k)
        
        # Expected shift: Δλ = 200 × (-0.005) = -1.0 nm
        expected_peak = base_peak - 1.0
        assert pytest.approx(shifted_peak, abs=0.01) == expected_peak
    
    def test_generate_temporal_series_with_function(self):
        """Test temporal series generation with infiltration function"""
        duration_s = 10.0
        interval_ms = 100.0  # 0.1 s
        
        # Linear infiltration: Δn(t) = 0.001 × t
        def infiltration_profile(t):
            return 0.001 * t
        
        time_points, spectra, peak_positions = generate_temporal_series(
            duration_s, interval_ms, infiltration_profile
        )
        
        # Check output shapes
        num_points = int(duration_s / (interval_ms / 1000.0)) + 1
        assert len(time_points) == num_points
        assert spectra.shape[0] == num_points
        assert spectra.shape[1] == 300  # Default wavelength resolution
        assert len(peak_positions) == num_points
        
        # Check time points
        assert time_points[0] == 0.0
        assert pytest.approx(time_points[-1], abs=0.01) == duration_s
        
        # Check peak positions increase over time (due to infiltration)
        assert peak_positions[-1] > peak_positions[0]
        
        # Check monotonic increase
        assert np.all(np.diff(peak_positions) >= 0)
    
    def test_generate_temporal_series_with_array(self):
        """Test temporal series generation with infiltration array"""
        duration_s = 5.0
        interval_ms = 500.0  # 0.5 s
        
        # Array of delta_n values
        num_points = int(duration_s / (interval_ms / 1000.0)) + 1
        infiltration_profile = np.linspace(0, 0.01, num_points)
        
        time_points, spectra, peak_positions = generate_temporal_series(
            duration_s, interval_ms, infiltration_profile
        )
        
        # Check output
        assert len(time_points) == num_points
        assert len(peak_positions) == num_points
        
        # Check peak shift matches expected values
        # At t=0: delta_n=0, peak should be at base_peak (520)
        assert pytest.approx(peak_positions[0], abs=0.1) == 520.0
        
        # At t=5s: delta_n=0.01, shift = 200 × 0.01 = 2.0 nm
        expected_final_peak = 520.0 + 2.0
        assert pytest.approx(peak_positions[-1], abs=0.1) == expected_final_peak
    
    def test_generate_temporal_series_custom_parameters(self):
        """Test temporal series with custom LSPR parameters"""
        duration_s = 2.0
        interval_ms = 200.0
        
        # Constant infiltration
        infiltration_profile = lambda t: 0.005
        
        base_peak = 540.0
        peak_width = 30.0
        amplitude = 2.0
        sensitivity_k = 150.0
        
        time_points, spectra, peak_positions = generate_temporal_series(
            duration_s,
            interval_ms,
            infiltration_profile,
            base_peak=base_peak,
            peak_width=peak_width,
            amplitude=amplitude,
            sensitivity_k=sensitivity_k
        )
        
        # Check peak position: 540 + 150 × 0.005 = 540.75 nm
        expected_peak = base_peak + sensitivity_k * 0.005
        assert pytest.approx(peak_positions[0], abs=0.1) == expected_peak
        
        # Check amplitude roughly matches (accounting for spectrum shape)
        assert np.max(spectra[0]) > amplitude * 0.9


class TestInfiltrationProfiles:
    """Test suite for infiltration profile functions"""

    def test_slow_infiltration_profile(self):
        """Test slow linear infiltration profile"""
        T = 3600.0  # 1 hour
        max_delta_n = 0.001
        
        # At t=0, delta_n should be 0
        delta_n = slow_infiltration_profile(0, T, max_delta_n)
        assert pytest.approx(delta_n, abs=1e-6) == 0.0
        
        # At t=T/2, delta_n should be max_delta_n/2
        delta_n = slow_infiltration_profile(T/2, T, max_delta_n)
        assert pytest.approx(delta_n, abs=1e-6) == max_delta_n / 2
        
        # At t=T, delta_n should be max_delta_n
        delta_n = slow_infiltration_profile(T, T, max_delta_n)
        assert pytest.approx(delta_n, abs=1e-6) == max_delta_n
        
        # Beyond T, should be capped at max_delta_n
        delta_n = slow_infiltration_profile(2*T, T, max_delta_n)
        assert pytest.approx(delta_n, abs=1e-6) == max_delta_n
    
    def test_fast_infiltration_profile(self):
        """Test fast exponential infiltration profile"""
        tau = 60.0  # 1 minute
        max_delta_n = 0.01
        
        # At t=0, delta_n should be 0
        delta_n = fast_infiltration_profile(0, tau, max_delta_n)
        assert pytest.approx(delta_n, abs=1e-6) == 0.0
        
        # At t=tau, delta_n should be ~0.632 * max_delta_n (1 - 1/e)
        delta_n = fast_infiltration_profile(tau, tau, max_delta_n)
        expected = max_delta_n * (1 - np.exp(-1))
        assert pytest.approx(delta_n, abs=1e-4) == expected
        
        # At t=5*tau, delta_n should be close to max_delta_n (>99%)
        delta_n = fast_infiltration_profile(5*tau, tau, max_delta_n)
        assert delta_n > 0.99 * max_delta_n
        
        # Should never exceed max_delta_n
        delta_n = fast_infiltration_profile(100*tau, tau, max_delta_n)
        assert delta_n <= max_delta_n
    
    def test_add_gaussian_noise_1d(self):
        """Test adding Gaussian noise to 1D spectrum"""
        # Create a clean spectrum
        wavelengths = np.linspace(400, 700, 300)
        spectrum = compute_lspr_spectrum(wavelengths, 520, 40, 1.0)
        
        # Add noise with seed for reproducibility
        sigma_noise = 0.05
        noisy_spectrum = add_gaussian_noise(spectrum, sigma_noise, seed=42)
        
        # Check shape preserved
        assert noisy_spectrum.shape == spectrum.shape
        
        # Check noise was added (values should differ)
        assert not np.allclose(noisy_spectrum, spectrum)
        
        # Check no negative values
        assert np.all(noisy_spectrum >= 0)
        
        # Check standard deviation of difference is roughly sigma_noise
        # (will be slightly less due to clipping at 0)
        diff = noisy_spectrum - spectrum
        assert 0.5 * sigma_noise < np.std(diff) < 1.5 * sigma_noise
    
    def test_add_gaussian_noise_2d(self):
        """Test adding Gaussian noise to 2D spectral time series"""
        # Create a temporal series
        duration_s = 5.0
        interval_ms = 500.0
        infiltration = lambda t: 0.001 * t
        
        time_points, spectra, _ = generate_temporal_series(
            duration_s, interval_ms, infiltration
        )
        
        # Add noise
        sigma_noise = 0.02
        noisy_spectra = add_gaussian_noise(spectra, sigma_noise, seed=123)
        
        # Check shape preserved
        assert noisy_spectra.shape == spectra.shape
        
        # Check noise was added
        assert not np.allclose(noisy_spectra, spectra)
        
        # Check no negative values
        assert np.all(noisy_spectra >= 0)
    
    def test_create_infiltration_profile_slow(self):
        """Test factory function for slow profile"""
        T = 7200.0  # 2 hours
        max_delta_n = 0.002
        
        profile = create_infiltration_profile("slow", T=T, max_delta_n=max_delta_n)
        
        # Test at various time points
        assert pytest.approx(profile(0), abs=1e-6) == 0.0
        assert pytest.approx(profile(T/2), abs=1e-6) == max_delta_n / 2
        assert pytest.approx(profile(T), abs=1e-6) == max_delta_n
    
    def test_create_infiltration_profile_fast(self):
        """Test factory function for fast profile"""
        tau = 120.0  # 2 minutes
        max_delta_n = 0.015
        
        profile = create_infiltration_profile("fast", tau=tau, max_delta_n=max_delta_n)
        
        # Test at various time points
        assert pytest.approx(profile(0), abs=1e-6) == 0.0
        assert profile(5*tau) > 0.99 * max_delta_n
    
    def test_create_infiltration_profile_defaults(self):
        """Test factory function with default parameters"""
        slow_profile = create_infiltration_profile("slow")
        fast_profile = create_infiltration_profile("fast")
        
        # Should use default values
        assert callable(slow_profile)
        assert callable(fast_profile)
        
        # Test they produce reasonable values
        assert 0 <= slow_profile(1800) <= 0.001
        assert 0 <= fast_profile(60) <= 0.01
    
    def test_create_infiltration_profile_invalid(self):
        """Test factory function with invalid profile type"""
        with pytest.raises(ValueError):
            create_infiltration_profile("invalid_type")
    
    def test_integration_temporal_series_with_profiles(self):
        """Integration test: temporal series with pre-defined profiles and noise"""
        # Use slow infiltration profile
        slow_profile = create_infiltration_profile("slow", T=10.0, max_delta_n=0.005)
        
        duration_s = 10.0
        interval_ms = 200.0
        
        # Generate clean series
        time_points, spectra, peak_positions = generate_temporal_series(
            duration_s, interval_ms, slow_profile
        )
        
        # Add noise
        noisy_spectra = add_gaussian_noise(spectra, sigma_noise=0.03, seed=42)
        
        # Verify output
        assert noisy_spectra.shape == spectra.shape
        assert len(peak_positions) == len(time_points)
        assert np.all(noisy_spectra >= 0)
        
        # Peak positions should show gradual shift
        assert peak_positions[-1] > peak_positions[0]
