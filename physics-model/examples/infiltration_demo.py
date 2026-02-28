"""
Demonstration of infiltration profiles for LSPR simulation

This script demonstrates the three types of infiltration profiles:
1. Slow linear infiltration (hours)
2. Fast exponential infiltration (minutes)
3. Adding Gaussian noise to spectra
"""

import numpy as np
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from lspr_simulator import (
    generate_temporal_series,
    slow_infiltration_profile,
    fast_infiltration_profile,
    add_gaussian_noise,
    create_infiltration_profile,
)


def demo_slow_infiltration():
    """Demonstrate slow linear infiltration over 1 hour"""
    print("\n=== Slow Linear Infiltration Demo ===")
    print("Profile: Δn(t) = 0.001 · t / T")
    print("Duration: 1 hour (3600 seconds)")
    
    # Create slow infiltration profile
    T = 3600.0  # 1 hour
    max_delta_n = 0.001
    slow_profile = create_infiltration_profile("slow", T=T, max_delta_n=max_delta_n)
    
    # Generate temporal series
    duration_s = 3600.0
    interval_ms = 60000.0  # 1 minute intervals
    
    time_points, spectra, peak_positions = generate_temporal_series(
        duration_s, interval_ms, slow_profile
    )
    
    print(f"Number of time points: {len(time_points)}")
    print(f"Initial peak position: {peak_positions[0]:.2f} nm")
    print(f"Final peak position: {peak_positions[-1]:.2f} nm")
    print(f"Total shift: {peak_positions[-1] - peak_positions[0]:.2f} nm")
    print(f"Spectral data shape: {spectra.shape}")
    
    return time_points, spectra, peak_positions


def demo_fast_infiltration():
    """Demonstrate fast exponential infiltration over minutes"""
    print("\n=== Fast Exponential Infiltration Demo ===")
    print("Profile: Δn(t) = 0.01 · (1 - e^(-t/τ))")
    print("Time constant τ: 60 seconds")
    
    # Create fast infiltration profile
    tau = 60.0  # 1 minute
    max_delta_n = 0.01
    fast_profile = create_infiltration_profile("fast", tau=tau, max_delta_n=max_delta_n)
    
    # Generate temporal series
    duration_s = 300.0  # 5 minutes
    interval_ms = 5000.0  # 5 second intervals
    
    time_points, spectra, peak_positions = generate_temporal_series(
        duration_s, interval_ms, fast_profile
    )
    
    print(f"Number of time points: {len(time_points)}")
    print(f"Initial peak position: {peak_positions[0]:.2f} nm")
    print(f"Peak at t=τ (60s): {peak_positions[12]:.2f} nm")
    print(f"Final peak position: {peak_positions[-1]:.2f} nm")
    print(f"Total shift: {peak_positions[-1] - peak_positions[0]:.2f} nm")
    print(f"Saturation level: {(peak_positions[-1] - peak_positions[0]) / (max_delta_n * 200) * 100:.1f}%")
    
    return time_points, spectra, peak_positions


def demo_noise_addition():
    """Demonstrate adding Gaussian noise to spectra"""
    print("\n=== Gaussian Noise Addition Demo ===")
    print("Noise: N(0, σ) with σ = 0.02")
    
    # Generate clean temporal series with slow infiltration
    slow_profile = create_infiltration_profile("slow", T=1800.0, max_delta_n=0.005)
    
    duration_s = 600.0  # 10 minutes
    interval_ms = 10000.0  # 10 second intervals
    
    time_points, clean_spectra, peak_positions = generate_temporal_series(
        duration_s, interval_ms, slow_profile
    )
    
    # Add noise
    sigma_noise = 0.02
    noisy_spectra = add_gaussian_noise(clean_spectra, sigma_noise, seed=42)
    
    print(f"Clean spectra shape: {clean_spectra.shape}")
    print(f"Noisy spectra shape: {noisy_spectra.shape}")
    print(f"Noise level (σ): {sigma_noise}")
    print(f"SNR at peak: {1.0 / sigma_noise:.1f}")
    
    # Calculate actual noise statistics
    noise_diff = noisy_spectra - clean_spectra
    print(f"Actual noise mean: {np.mean(noise_diff):.6f}")
    print(f"Actual noise std: {np.std(noise_diff):.6f}")
    
    return time_points, clean_spectra, noisy_spectra


def demo_custom_profile():
    """Demonstrate custom infiltration profile"""
    print("\n=== Custom Infiltration Profile Demo ===")
    print("Profile: Step function with oscillations")
    
    # Define custom infiltration function
    def custom_infiltration(t):
        """Step + sinusoidal oscillation"""
        if t < 60:
            return 0.0
        else:
            base = 0.008
            oscillation = 0.002 * np.sin(2 * np.pi * t / 120)
            return base + oscillation
    
    # Generate temporal series
    duration_s = 300.0
    interval_ms = 2000.0  # 2 second intervals
    
    time_points, spectra, peak_positions = generate_temporal_series(
        duration_s, interval_ms, custom_infiltration
    )
    
    print(f"Number of time points: {len(time_points)}")
    print(f"Initial peak position: {peak_positions[0]:.2f} nm")
    print(f"Peak after step (t=60s): {peak_positions[30]:.2f} nm")
    print(f"Max peak position: {np.max(peak_positions):.2f} nm")
    print(f"Min peak position: {np.min(peak_positions):.2f} nm")
    
    return time_points, spectra, peak_positions


def main():
    """Run all demonstrations"""
    print("=" * 60)
    print("LSPR Infiltration Profile Demonstrations")
    print("=" * 60)
    
    # Run demos
    demo_slow_infiltration()
    demo_fast_infiltration()
    demo_noise_addition()
    demo_custom_profile()
    
    print("\n" + "=" * 60)
    print("All demonstrations completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
