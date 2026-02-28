# Infiltration Profiles for LSPR Simulation

This document describes the infiltration profile functions implemented for simulating water infiltration in LSPR-based nanoparticle sensors.

## Overview

Infiltration profiles model how the refractive index changes over time as water (or other contaminants) infiltrate the sensing medium. These profiles are used with the `generate_temporal_series()` function to create realistic time-dependent spectral data.

## Profile Types

### 1. Slow Linear Infiltration

**Function:** `slow_infiltration_profile(t, T, max_delta_n)`

**Mathematical Model:**
$$\Delta n(t) = \Delta n_{\max} \cdot \frac{t}{T}$$

**Characteristics:**
- Linear progression over hours
- Models gradual, steady infiltration
- Suitable for long-term monitoring scenarios

**Parameters:**
- `t`: Current time (seconds)
- `T`: Total duration for full infiltration (default: 3600s = 1 hour)
- `max_delta_n`: Maximum refractive index change (default: 0.001)

**Example:**
```python
from lspr_simulator import create_infiltration_profile, generate_temporal_series

# Create slow infiltration over 2 hours
slow_profile = create_infiltration_profile("slow", T=7200, max_delta_n=0.002)

# Generate data
time_points, spectra, peaks = generate_temporal_series(
    duration_s=7200,
    interval_ms=60000,  # 1 minute intervals
    infiltration_profile=slow_profile
)
```

### 2. Fast Exponential Infiltration

**Function:** `fast_infiltration_profile(t, tau, max_delta_n)`

**Mathematical Model:**
$$\Delta n(t) = \Delta n_{\max} \cdot (1 - e^{-t/\tau})$$

**Characteristics:**
- Exponential saturation over minutes
- Models rapid initial infiltration that slows down
- Time constant τ controls saturation speed
- Suitable for acute contamination events

**Parameters:**
- `t`: Current time (seconds)
- `tau`: Time constant τ (default: 60s = 1 minute)
- `max_delta_n`: Maximum refractive index change (default: 0.01)

**Physical Interpretation:**
- At t = τ: reaches ~63.2% of maximum
- At t = 3τ: reaches ~95% of maximum
- At t = 5τ: reaches ~99.3% of maximum

**Example:**
```python
# Create fast infiltration with 2-minute time constant
fast_profile = create_infiltration_profile("fast", tau=120, max_delta_n=0.015)

# Generate data
time_points, spectra, peaks = generate_temporal_series(
    duration_s=600,  # 10 minutes
    interval_ms=5000,  # 5 second intervals
    infiltration_profile=fast_profile
)
```

### 3. Gaussian Noise

**Function:** `add_gaussian_noise(spectra, sigma_noise, seed)`

**Mathematical Model:**
$$I_{\text{noisy}}(\lambda) = I(\lambda) + \mathcal{N}(0, \sigma_{\text{noise}})$$

**Characteristics:**
- Adds independent Gaussian noise to each wavelength point
- Models measurement uncertainty and environmental fluctuations
- Negative values are clipped to zero (physical constraint)

**Parameters:**
- `spectra`: Spectral data (1D or 2D array)
- `sigma_noise`: Standard deviation of noise
- `seed`: Random seed for reproducibility (optional)

**Typical Noise Levels:**
- σ = 0.01: High-quality measurement (SNR ≈ 100)
- σ = 0.02: Good measurement (SNR ≈ 50)
- σ = 0.05: Moderate noise (SNR ≈ 20)
- σ = 0.10: High noise (SNR ≈ 10)

**Example:**
```python
from lspr_simulator import add_gaussian_noise

# Generate clean spectra
time_points, clean_spectra, peaks = generate_temporal_series(
    duration_s=300,
    interval_ms=1000,
    infiltration_profile=slow_profile
)

# Add realistic noise
noisy_spectra = add_gaussian_noise(clean_spectra, sigma_noise=0.02, seed=42)
```

## Factory Function

**Function:** `create_infiltration_profile(profile_type, **kwargs)`

Convenience factory for creating infiltration profile functions.

**Parameters:**
- `profile_type`: "slow" or "fast"
- `**kwargs`: Profile-specific parameters

**Returns:** Callable function f(t) → Δn

**Example:**
```python
# Create profiles
slow = create_infiltration_profile("slow", T=3600, max_delta_n=0.001)
fast = create_infiltration_profile("fast", tau=60, max_delta_n=0.01)

# Use directly
delta_n_at_10min = slow(600)  # Get Δn at t=600s
```

## Custom Profiles

You can define custom infiltration profiles as Python functions:

```python
def custom_profile(t):
    """Custom infiltration with step change and oscillation"""
    if t < 60:
        return 0.0
    else:
        base = 0.008
        oscillation = 0.002 * np.sin(2 * np.pi * t / 120)
        return base + oscillation

# Use with generate_temporal_series
time_points, spectra, peaks = generate_temporal_series(
    duration_s=300,
    interval_ms=2000,
    infiltration_profile=custom_profile
)
```

## Complete Example

```python
import numpy as np
from lspr_simulator import (
    generate_temporal_series,
    create_infiltration_profile,
    add_gaussian_noise
)

# 1. Create fast infiltration profile
infiltration = create_infiltration_profile(
    "fast", 
    tau=90,           # 1.5 minute time constant
    max_delta_n=0.012 # Significant infiltration
)

# 2. Generate temporal series
duration_s = 600      # 10 minutes total
interval_ms = 2000    # 2 second intervals

time_points, clean_spectra, peak_positions = generate_temporal_series(
    duration_s=duration_s,
    interval_ms=interval_ms,
    infiltration_profile=infiltration,
    base_peak=520.0,
    peak_width=40.0,
    sensitivity_k=200.0
)

# 3. Add realistic noise
noisy_spectra = add_gaussian_noise(clean_spectra, sigma_noise=0.03, seed=42)

# 4. Analyze results
print(f"Time points: {len(time_points)}")
print(f"Initial peak: {peak_positions[0]:.2f} nm")
print(f"Final peak: {peak_positions[-1]:.2f} nm")
print(f"Total shift: {peak_positions[-1] - peak_positions[0]:.2f} nm")
```

## Physical Interpretation

### Refractive Index Changes

Typical refractive indices:
- Water: n ≈ 1.33
- Ethanol: n ≈ 1.36
- Glycerol: n ≈ 1.47

For water infiltration into a medium:
- Δn = 0.001: Minor contamination (~0.075% change)
- Δn = 0.01: Moderate contamination (~0.75% change)
- Δn = 0.1: Major contamination (~7.5% change)

### LSPR Sensitivity

For gold nanoparticles:
- Typical sensitivity: k ≈ 200 nm/RIU
- Wavelength shift: Δλ = k × Δn
- Example: Δn = 0.01 → Δλ = 2 nm

## References

- Sensitivity values based on typical Au nanoparticle LSPR sensors
- Exponential infiltration model follows Fickian diffusion behavior
- Linear model approximates constant flux scenarios
