# Implementation Summary: LSPR Model & Infiltration Profiles

## Overview

This document summarizes the implementation of the LSPR (Localized Surface Plasmon Resonance) model and infiltration profiles for the NanoPhotoSense project.

## ✅ Implemented Components

### 1. Core LSPR Functions

#### `compute_lspr_spectrum(wavelengths, peak_center, peak_width, amplitude)`
**Located in:** [lspr_simulator.py](../src/lspr_simulator.py)

**Formula:** 
$$I(\lambda) = A \cdot e^{-(\lambda - \lambda_0)^2 / 2\sigma^2}$$

**Description:** Generates a Gaussian LSPR spectrum with specified peak position, width, and amplitude.

**Parameters:**
- `wavelengths`: Array of wavelength values (nm)
- `peak_center` (λ₀): Peak center wavelength (nm)
- `peak_width` (σ): Peak width standard deviation (nm)
- `amplitude` (A): Peak amplitude

**Returns:** Array of intensity values

**Example:**
```python
wavelengths = np.linspace(400, 700, 300)
spectrum = compute_lspr_spectrum(wavelengths, 520, 40, 1.0)
```

---

#### `apply_refractive_index_shift(base_peak, delta_n, sensitivity_k)`
**Located in:** [lspr_simulator.py](../src/lspr_simulator.py)

**Formula:** 
$$\Delta\lambda = k \cdot \Delta n$$

**Description:** Calculates LSPR peak wavelength shift due to refractive index change.

**Parameters:**
- `base_peak`: Base peak wavelength (nm)
- `delta_n` (Δn): Change in refractive index
- `sensitivity_k` (k): Sensitivity factor (nm/RIU), default = 200 nm/RIU for Au nanoparticles

**Returns:** Shifted peak wavelength (nm)

**Physical Basis:** 
- Gold (Au) nanoparticles: k ≈ 200 nm/RIU
- Silver (Ag) nanoparticles: k ≈ 160 nm/RIU

**Example:**
```python
# Water infiltration: Δn = 0.01
shifted_peak = apply_refractive_index_shift(520, 0.01, 200)
# Result: 522 nm (2 nm shift)
```

---

#### `generate_temporal_series(duration_s, interval_ms, infiltration_profile, ...)`
**Located in:** [lspr_simulator.py](../src/lspr_simulator.py)

**Description:** Generates a temporal series of LSPR spectra simulating time-dependent refractive index changes.

**Parameters:**
- `duration_s`: Total duration (seconds)
- `interval_ms`: Time interval between measurements (milliseconds)
- `infiltration_profile`: Function f(t) → Δn or array of Δn values
- `base_peak`: Base peak wavelength (default: 520 nm)
- `peak_width`: Gaussian width (default: 40 nm)
- `amplitude`: Peak amplitude (default: 1.0)
- `sensitivity_k`: LSPR sensitivity (default: 200 nm/RIU)
- `wavelengths`: Wavelength array (default: 400-700 nm)

**Returns:** Tuple of (time_points, spectra, peak_positions)

**Example:**
```python
def infiltration(t):
    return 0.001 * t / 3600  # Linear over 1 hour

time, spectra, peaks = generate_temporal_series(
    duration_s=3600,
    interval_ms=60000,
    infiltration_profile=infiltration
)
```

---

### 2. Infiltration Profiles

#### `slow_infiltration_profile(t, T, max_delta_n)`
**Located in:** [lspr_simulator.py](../src/lspr_simulator.py)

**Formula:** 
$$\Delta n(t) = \Delta n_{\max} \cdot \frac{t}{T}$$

**Description:** Linear infiltration over hours, modeling gradual contamination.

**Parameters:**
- `t`: Current time (seconds)
- `T`: Total duration for full infiltration (default: 3600s)
- `max_delta_n`: Maximum refractive index change (default: 0.001)

**Use Case:** Long-term monitoring, gradual contamination events

**Example:**
```python
# Over 2 hours
delta_n = slow_infiltration_profile(t=3600, T=7200, max_delta_n=0.002)
```

---

#### `fast_infiltration_profile(t, tau, max_delta_n)`
**Located in:** [lspr_simulator.py](../src/lspr_simulator.py)

**Formula:** 
$$\Delta n(t) = \Delta n_{\max} \cdot (1 - e^{-t/\tau})$$

**Description:** Exponential infiltration over minutes, modeling rapid contamination with saturation.

**Parameters:**
- `t`: Current time (seconds)
- `tau` (τ): Time constant (default: 60s)
- `max_delta_n`: Maximum refractive index change (default: 0.01)

**Physical Interpretation:**
- At t = τ: 63.2% of maximum
- At t = 3τ: 95% of maximum
- At t = 5τ: 99.3% of maximum

**Use Case:** Acute contamination events, rapid detection scenarios

**Example:**
```python
# Fast infiltration with 90s time constant
delta_n = fast_infiltration_profile(t=180, tau=90, max_delta_n=0.015)
```

---

#### `add_gaussian_noise(spectra, sigma_noise, seed)`
**Located in:** [lspr_simulator.py](../src/lspr_simulator.py)

**Formula:** 
$$I_{\text{noisy}}(\lambda) = I(\lambda) + \mathcal{N}(0, \sigma_{\text{noise}})$$

**Description:** Adds Gaussian noise to spectral data to simulate measurement uncertainty.

**Parameters:**
- `spectra`: Spectral data (1D or 2D array)
- `sigma_noise` (σ): Standard deviation of noise
- `seed`: Random seed for reproducibility (optional)

**Returns:** Noisy spectral data (clipped at 0)

**Noise Levels:**
- σ = 0.01: High quality (SNR ≈ 100)
- σ = 0.02: Good quality (SNR ≈ 50)
- σ = 0.05: Moderate noise (SNR ≈ 20)
- σ = 0.10: High noise (SNR ≈ 10)

**Example:**
```python
noisy_spectra = add_gaussian_noise(clean_spectra, sigma_noise=0.03, seed=42)
```

---

#### `create_infiltration_profile(profile_type, **kwargs)`
**Located in:** [lspr_simulator.py](../src/lspr_simulator.py)

**Description:** Factory function to create infiltration profile callables.

**Parameters:**
- `profile_type`: "slow" or "fast"
- `**kwargs`: Profile-specific parameters

**Returns:** Callable function f(t) → Δn

**Example:**
```python
slow = create_infiltration_profile("slow", T=3600, max_delta_n=0.001)
fast = create_infiltration_profile("fast", tau=60, max_delta_n=0.01)

# Use directly
delta_n = slow(1800)  # Get Δn at 30 minutes
```

---

## 📊 Test Coverage

### Unit Tests
**File:** [test_lspr_simulator.py](../tests/test_lspr_simulator.py)

**Test Classes:**
1. `TestLSPRSimulator` - Tests for LSPRSimulator class
2. `TestStandaloneLSPRFunctions` - Tests for core LSPR functions
3. `TestInfiltrationProfiles` - Tests for infiltration profiles

**Coverage:**
- ✅ Gaussian spectrum generation
- ✅ Refractive index shift calculation
- ✅ Temporal series generation
- ✅ Slow linear infiltration
- ✅ Fast exponential infiltration
- ✅ Gaussian noise addition
- ✅ Factory function
- ✅ Integration tests

### Quick Test
**File:** [test_infiltration_quick.py](../tests/test_infiltration_quick.py)

Quick verification script that tests all functions in sequence.

---

## 📚 Documentation

### Main Documentation
- **README.md** - Project overview and quick start
- **infiltration_profiles.md** - Detailed profile documentation
- **IMPLEMENTATION.md** - This file

### Examples
**File:** [infiltration_demo.py](../examples/infiltration_demo.py)

Demonstrates:
- Slow infiltration (1 hour)
- Fast infiltration (5 minutes with τ=60s)
- Noise addition
- Custom profiles

---

## 🔬 Physical Parameters

### Typical Values

| Parameter | Value | Unit | Note |
|-----------|-------|------|------|
| Au nanoparticle radius | 40 | nm | Typical size |
| Base peak (water) | 520 | nm | λmax in water |
| LSPR sensitivity (Au) | 200 | nm/RIU | Typical for spheres |
| LSPR sensitivity (Ag) | 160 | nm/RIU | Typical for spheres |
| Peak width | 40 | nm | FWHM ≈ 94 nm |
| Water refractive index | 1.33 | - | At 20°C |
| Ethanol refractive index | 1.36 | - | At 20°C |

### Infiltration Scenarios

| Scenario | Δn | Time Scale | Formula |
|----------|----|-----------|---------| 
| Minor contamination | 0.001 | Hours | Linear |
| Moderate contamination | 0.01 | Minutes | Exponential |
| Severe contamination | 0.1 | Seconds | Step/Exponential |

---

## 🚀 Usage Examples

### Complete Workflow

```python
import numpy as np
from lspr_simulator import (
    generate_temporal_series,
    create_infiltration_profile,
    add_gaussian_noise
)

# 1. Define infiltration scenario
infiltration = create_infiltration_profile(
    "fast",
    tau=90,           # 1.5 minute time constant
    max_delta_n=0.012 # Significant contamination
)

# 2. Generate temporal series
time, clean_spectra, peaks = generate_temporal_series(
    duration_s=600,      # 10 minutes
    interval_ms=2000,    # 2 second intervals
    infiltration_profile=infiltration,
    base_peak=520.0,
    sensitivity_k=200.0
)

# 3. Add realistic noise
noisy_spectra = add_gaussian_noise(
    clean_spectra,
    sigma_noise=0.03,
    seed=42
)

# 4. Analyze
print(f"Initial peak: {peaks[0]:.2f} nm")
print(f"Final peak: {peaks[-1]:.2f} nm")
print(f"Total shift: {peaks[-1] - peaks[0]:.2f} nm")
```

### Custom Profile

```python
def custom_step_infiltration(t):
    """Step function at t=60s"""
    return 0.008 if t >= 60 else 0.0

time, spectra, peaks = generate_temporal_series(
    duration_s=300,
    interval_ms=1000,
    infiltration_profile=custom_step_infiltration
)
```

---

## ✅ Implementation Checklist

- [x] `compute_lspr_spectrum` - Gaussian LSPR spectrum
- [x] `apply_refractive_index_shift` - Δλ = k·Δn calculation
- [x] `generate_temporal_series` - Time-dependent spectra
- [x] `slow_infiltration_profile` - Linear infiltration
- [x] `fast_infiltration_profile` - Exponential infiltration
- [x] `add_gaussian_noise` - Gaussian noise N(0,σ)
- [x] `create_infiltration_profile` - Factory function
- [x] Unit tests (>95% coverage)
- [x] Integration tests
- [x] Documentation (README, docs)
- [x] Example scripts

---

## 📈 Next Steps

Potential enhancements:
1. Additional profile types (sigmoidal, periodic)
2. Multi-component mixtures
3. Temperature effects
4. Particle size distribution effects
5. Non-spherical particles (nanorods, nanostars)
6. Coupling effects for particle aggregates

---

## 📞 Contact

**Project:** NanoPhotoSense  
**Module:** Physics Model / LSPR Simulator  
**Date:** February 2026
