"""
LSPR (Localized Surface Plasmon Resonance) Physics Simulator
Models nanoparticle optical response to environmental changes
"""

import numpy as np
from scipy.signal import find_peaks
from typing import Tuple, Optional


class LSPRSimulator:
    """
    Simulates LSPR spectral response for gold nanoparticles in varying
    refractive index environments.
    """

    def __init__(
        self,
        particle_radius: float = 40.0,  # nm
        baseline_peak: float = 520.0,  # nm
        sensitivity: float = 60.0,  # nm/RIU (Refractive Index Unit)
    ):
        """
        Initialize LSPR simulator with nanoparticle parameters.

        Args:
            particle_radius: Radius of gold nanoparticles (nm)
            baseline_peak: Peak wavelength in baseline environment (nm)
            sensitivity: Sensitivity to refractive index changes (nm/RIU)
        """
        self.particle_radius = particle_radius
        self.baseline_peak = baseline_peak
        self.sensitivity = sensitivity
        self.baseline_n = 1.33  # Water refractive index

    def calculate_peak_shift(self, refractive_index: float) -> float:
        """
        Calculate LSPR peak wavelength shift due to refractive index change.

        Args:
            refractive_index: Current medium refractive index

        Returns:
            Peak wavelength shift (nm)
        """
        delta_n = refractive_index - self.baseline_n
        return self.sensitivity * delta_n

    def generate_spectrum(
        self,
        refractive_index: float,
        wavelengths: Optional[np.ndarray] = None,
        noise_level: float = 0.02,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate a complete LSPR absorption spectrum.

        Args:
            refractive_index: Medium refractive index
            wavelengths: Wavelength range (nm), defaults to 400-700 nm
            noise_level: Gaussian noise level (fraction of peak intensity)

        Returns:
            Tuple of (wavelengths, intensities)
        """
        if wavelengths is None:
            wavelengths = np.linspace(400, 700, 300)

        # Calculate shifted peak position
        peak_shift = self.calculate_peak_shift(refractive_index)
        peak_wavelength = self.baseline_peak + peak_shift

        # Lorentzian line shape for LSPR
        gamma = 40.0  # Line width (nm)
        intensities = 1.0 / (1.0 + ((wavelengths - peak_wavelength) / gamma) ** 2)

        # Add Gaussian noise
        if noise_level > 0:
            noise = np.random.normal(0, noise_level, len(wavelengths))
            intensities += noise
            intensities = np.clip(intensities, 0, None)

        return wavelengths, intensities

    def detect_peak_wavelength(self, wavelengths: np.ndarray, intensities: np.ndarray) -> float:
        """
        Detect peak wavelength from spectrum using peak finding.

        Args:
            wavelengths: Wavelength array
            intensities: Intensity array

        Returns:
            Peak wavelength (nm)
        """
        peaks, _ = find_peaks(intensities, prominence=0.1)
        if len(peaks) == 0:
            # Fallback to maximum
            peak_idx = np.argmax(intensities)
        else:
            # Take highest peak
            peak_idx = peaks[np.argmax(intensities[peaks])]

        return wavelengths[peak_idx]

    def calculate_delta_n(self, peak_wavelength: float) -> float:
        """
        Calculate refractive index change from observed peak wavelength.

        Args:
            peak_wavelength: Observed peak wavelength (nm)

        Returns:
            Refractive index change (Δn)
        """
        shift = peak_wavelength - self.baseline_peak
        return shift / self.sensitivity

    def calculate_risk_score(self, delta_n: float, threshold: float = 0.01) -> float:
        """
        Calculate contamination risk score from refractive index change.

        Args:
            delta_n: Refractive index change
            threshold: Threshold for significant change

        Returns:
            Risk score (0-100)
        """
        # Sigmoid-based scoring
        normalized = abs(delta_n) / threshold
        risk = 100 * (1 - 1 / (1 + normalized**2))
        return min(risk, 100.0)


# Standalone LSPR modeling functions

def compute_lspr_spectrum(
    wavelengths: np.ndarray,
    peak_center: float,
    peak_width: float,
    amplitude: float
) -> np.ndarray:
    """
    Generate a Gaussian LSPR spectrum.
    
    Uses the formula: I(λ) = A · exp(-(λ - λ₀)² / (2σ²))
    
    Args:
        wavelengths: Array of wavelength values (nm)
        peak_center: Peak center wavelength λ₀ (nm)
        peak_width: Peak width σ (nm)
        amplitude: Peak amplitude A
    
    Returns:
        Array of intensity values corresponding to input wavelengths
    """
    # Gaussian profile: I(λ) = A · exp(-(λ - λ₀)² / (2σ²))
    exponent = -((wavelengths - peak_center) ** 2) / (2 * peak_width ** 2)
    intensities = amplitude * np.exp(exponent)
    return intensities


def apply_refractive_index_shift(
    base_peak: float,
    delta_n: float,
    sensitivity_k: float = 200.0
) -> float:
    """
    Calculate LSPR peak wavelength shift due to refractive index change.
    
    Uses the formula: Δλ = k · Δn
    where k ≈ 200 nm/RIU (typical for Au nanoparticles)
    
    Args:
        base_peak: Base peak wavelength (nm)
        delta_n: Change in refractive index (Δn)
        sensitivity_k: Sensitivity factor k (nm/RIU), default 200 nm/RIU for Au
    
    Returns:
        Shifted peak wavelength (nm)
    """
    # Calculate wavelength shift: Δλ = k · Δn
    delta_lambda = sensitivity_k * delta_n
    
    # Return new peak position
    shifted_peak = base_peak + delta_lambda
    return shifted_peak


def generate_temporal_series(
    duration_s: float,
    interval_ms: float,
    infiltration_profile,
    base_peak: float = 520.0,
    peak_width: float = 40.0,
    amplitude: float = 1.0,
    sensitivity_k: float = 200.0,
    wavelengths: Optional[np.ndarray] = None
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Generate temporal series of LSPR spectra simulating water infiltration.
    
    Models time-dependent refractive index changes Δn(t) that simulate
    progressive water infiltration into a sensing medium.
    
    Args:
        duration_s: Total duration of simulation (seconds)
        interval_ms: Time interval between measurements (milliseconds)
        infiltration_profile: Function or array defining Δn(t) evolution
                            - If callable: function(t) -> delta_n
                            - If array-like: array of delta_n values
        base_peak: Base peak wavelength (nm), default 520 nm
        peak_width: Gaussian peak width σ (nm), default 40 nm
        amplitude: Peak amplitude, default 1.0
        sensitivity_k: LSPR sensitivity (nm/RIU), default 200 nm/RIU
        wavelengths: Wavelength array (nm), defaults to 400-700 nm
    
    Returns:
        Tuple of:
        - time_points: Array of time points (seconds)
        - spectra: 2D array of spectra (time × wavelength)
        - peak_positions: Array of peak wavelengths at each time point (nm)
    """
    # Setup wavelength range
    if wavelengths is None:
        wavelengths = np.linspace(400, 700, 300)
    
    # Calculate time points
    interval_s = interval_ms / 1000.0
    num_points = int(duration_s / interval_s) + 1
    time_points = np.linspace(0, duration_s, num_points)
    
    # Initialize output arrays
    spectra = np.zeros((num_points, len(wavelengths)))
    peak_positions = np.zeros(num_points)
    
    # Generate infiltration profile if needed
    if callable(infiltration_profile):
        # Function provided: evaluate at each time point
        delta_n_values = np.array([infiltration_profile(t) for t in time_points])
    else:
        # Array provided: interpolate if necessary
        delta_n_array = np.array(infiltration_profile)
        if len(delta_n_array) == num_points:
            delta_n_values = delta_n_array
        else:
            # Interpolate to match time points
            original_times = np.linspace(0, duration_s, len(delta_n_array))
            delta_n_values = np.interp(time_points, original_times, delta_n_array)
    
    # Generate spectrum at each time point
    for i, (t, delta_n) in enumerate(zip(time_points, delta_n_values)):
        # Calculate shifted peak position
        current_peak = apply_refractive_index_shift(base_peak, delta_n, sensitivity_k)
        peak_positions[i] = current_peak
        
        # Generate spectrum
        spectra[i, :] = compute_lspr_spectrum(
            wavelengths,
            current_peak,
            peak_width,
            amplitude
        )
    
    return time_points, spectra, peak_positions


# Infiltration profile functions

def slow_infiltration_profile(t: float, T: float = 3600.0, max_delta_n: float = 0.001) -> float:
    """
    Slow linear infiltration profile.
    
    Models gradual water infiltration over hours with linear progression:
    Δn(t) = max_delta_n · (t / T)
    
    Args:
        t: Current time (seconds)
        T: Total duration for full infiltration (seconds), default 3600s (1 hour)
        max_delta_n: Maximum refractive index change, default 0.001
    
    Returns:
        Refractive index change at time t
    """
    delta_n = max_delta_n * (t / T)
    return min(delta_n, max_delta_n)  # Cap at max_delta_n


def fast_infiltration_profile(t: float, tau: float = 60.0, max_delta_n: float = 0.01) -> float:
    """
    Fast exponential infiltration profile.
    
    Models rapid water infiltration over minutes with exponential saturation:
    Δn(t) = max_delta_n · (1 - e^(-t/τ))
    
    Args:
        t: Current time (seconds)
        tau: Time constant τ (seconds), default 60s (1 minute)
        max_delta_n: Maximum refractive index change, default 0.01
    
    Returns:
        Refractive index change at time t
    """
    delta_n = max_delta_n * (1.0 - np.exp(-t / tau))
    return delta_n


def add_gaussian_noise(
    spectra: np.ndarray,
    sigma_noise: float = 0.01,
    seed: Optional[int] = None
) -> np.ndarray:
    """
    Add Gaussian noise to spectral data.
    
    Adds independent Gaussian noise N(0, σ_noise) to each spectrum point:
    I_noisy(λ) = I(λ) + N(0, σ_noise)
    
    Args:
        spectra: Spectral data array (can be 1D or 2D)
                - 1D: single spectrum (wavelength,)
                - 2D: time series (time, wavelength)
        sigma_noise: Standard deviation of Gaussian noise
        seed: Random seed for reproducibility (optional)
    
    Returns:
        Noisy spectral data with same shape as input
    """
    if seed is not None:
        np.random.seed(seed)
    
    # Generate Gaussian noise with same shape as input
    noise = np.random.normal(0, sigma_noise, spectra.shape)
    
    # Add noise to spectra
    noisy_spectra = spectra + noise
    
    # Clip negative values (intensities should be non-negative)
    noisy_spectra = np.clip(noisy_spectra, 0, None)
    
    return noisy_spectra


def create_infiltration_profile(
    profile_type: str = "slow",
    **kwargs
):
    """
    Factory function to create infiltration profile functions.
    
    Args:
        profile_type: Type of infiltration profile ("slow" or "fast")
        **kwargs: Parameters for the specific profile type
                  - slow: T (duration), max_delta_n
                  - fast: tau (time constant), max_delta_n
    
    Returns:
        Callable infiltration profile function that takes time t and returns delta_n
    
    Examples:
        >>> slow_profile = create_infiltration_profile("slow", T=7200, max_delta_n=0.002)
        >>> fast_profile = create_infiltration_profile("fast", tau=120, max_delta_n=0.015)
    """
    if profile_type.lower() == "slow":
        T = kwargs.get("T", 3600.0)
        max_delta_n = kwargs.get("max_delta_n", 0.001)
        return lambda t: slow_infiltration_profile(t, T, max_delta_n)
    
    elif profile_type.lower() == "fast":
        tau = kwargs.get("tau", 60.0)
        max_delta_n = kwargs.get("max_delta_n", 0.01)
        return lambda t: fast_infiltration_profile(t, tau, max_delta_n)
    
    else:
        raise ValueError(f"Unknown profile type: {profile_type}. Use 'slow' or 'fast'.")
