"""
Quick test script for infiltration profiles
Tests all three profile types and ensures they work correctly
"""

import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from lspr_simulator import (
    compute_lspr_spectrum,
    apply_refractive_index_shift,
    generate_temporal_series,
    slow_infiltration_profile,
    fast_infiltration_profile,
    add_gaussian_noise,
    create_infiltration_profile
)

def test_basic_functions():
    """Test basic LSPR functions"""
    print("Testing basic LSPR functions...")
    
    # Test compute_lspr_spectrum
    wavelengths = np.linspace(400, 700, 300)
    spectrum = compute_lspr_spectrum(wavelengths, 520, 40, 1.0)
    assert len(spectrum) == 300
    assert np.max(spectrum) <= 1.0
    print("✓ compute_lspr_spectrum works")
    
    # Test apply_refractive_index_shift
    shifted_peak = apply_refractive_index_shift(520, 0.01, 200)
    assert shifted_peak == 522.0
    print("✓ apply_refractive_index_shift works")
    
    print()

def test_slow_infiltration():
    """Test slow linear infiltration"""
    print("Testing slow infiltration profile...")
    
    T = 3600.0
    max_delta_n = 0.001
    
    # Test at different time points
    assert slow_infiltration_profile(0, T, max_delta_n) == 0.0
    assert abs(slow_infiltration_profile(T/2, T, max_delta_n) - max_delta_n/2) < 1e-6
    assert abs(slow_infiltration_profile(T, T, max_delta_n) - max_delta_n) < 1e-6
    
    print("✓ Slow infiltration profile works")
    print(f"  - At t=0: Δn = 0.000")
    print(f"  - At t=T/2: Δn = {max_delta_n/2:.6f}")
    print(f"  - At t=T: Δn = {max_delta_n:.6f}")
    print()

def test_fast_infiltration():
    """Test fast exponential infiltration"""
    print("Testing fast infiltration profile...")
    
    tau = 60.0
    max_delta_n = 0.01
    
    # Test at different time points
    assert fast_infiltration_profile(0, tau, max_delta_n) == 0.0
    
    delta_at_tau = fast_infiltration_profile(tau, tau, max_delta_n)
    expected_at_tau = max_delta_n * (1 - np.exp(-1))
    assert abs(delta_at_tau - expected_at_tau) < 1e-6
    
    delta_at_5tau = fast_infiltration_profile(5*tau, tau, max_delta_n)
    assert delta_at_5tau > 0.99 * max_delta_n
    
    print("✓ Fast infiltration profile works")
    print(f"  - At t=0: Δn = 0.000000")
    print(f"  - At t=τ: Δn = {delta_at_tau:.6f} (63.2% of max)")
    print(f"  - At t=5τ: Δn = {delta_at_5tau:.6f} (99.3% of max)")
    print()

def test_temporal_series():
    """Test temporal series generation"""
    print("Testing temporal series generation...")
    
    # Create slow profile
    profile = create_infiltration_profile("slow", T=100, max_delta_n=0.005)
    
    # Generate series
    time, spectra, peaks = generate_temporal_series(100, 1000, profile)
    
    assert len(time) == len(peaks)
    assert spectra.shape[0] == len(time)
    assert spectra.shape[1] == 300  # Default wavelengths
    assert peaks[-1] > peaks[0]  # Peak should shift
    
    print("✓ Temporal series generation works")
    print(f"  - Time points: {len(time)}")
    print(f"  - Spectra shape: {spectra.shape}")
    print(f"  - Peak shift: {peaks[-1] - peaks[0]:.3f} nm")
    print()

def test_noise_addition():
    """Test Gaussian noise addition"""
    print("Testing Gaussian noise addition...")
    
    wavelengths = np.linspace(400, 700, 300)
    clean_spectrum = compute_lspr_spectrum(wavelengths, 520, 40, 1.0)
    
    # Add noise
    sigma = 0.02
    noisy = add_gaussian_noise(clean_spectrum, sigma, seed=42)
    
    assert noisy.shape == clean_spectrum.shape
    assert not np.allclose(noisy, clean_spectrum)
    assert np.all(noisy >= 0)  # No negative values
    
    noise = noisy - clean_spectrum
    std_noise = np.std(noise)
    
    print("✓ Gaussian noise addition works")
    print(f"  - Target σ: {sigma:.4f}")
    print(f"  - Actual σ: {std_noise:.4f}")
    print(f"  - SNR: {1/sigma:.1f}")
    print()

def test_factory_function():
    """Test profile factory function"""
    print("Testing profile factory function...")
    
    slow = create_infiltration_profile("slow", T=3600, max_delta_n=0.001)
    fast = create_infiltration_profile("fast", tau=60, max_delta_n=0.01)
    
    assert callable(slow)
    assert callable(fast)
    
    # Test they return reasonable values
    assert 0 <= slow(1800) <= 0.001
    assert 0 <= fast(60) <= 0.01
    
    print("✓ Profile factory function works")
    print(f"  - Slow profile at t=1800s: Δn = {slow(1800):.6f}")
    print(f"  - Fast profile at t=60s: Δn = {fast(60):.6f}")
    print()

def main():
    print("=" * 60)
    print("INFILTRATION PROFILES TEST SUITE")
    print("=" * 60)
    print()
    
    test_basic_functions()
    test_slow_infiltration()
    test_fast_infiltration()
    test_temporal_series()
    test_noise_addition()
    test_factory_function()
    
    print("=" * 60)
    print("✓ ALL TESTS PASSED!")
    print("=" * 60)

if __name__ == "__main__":
    main()
