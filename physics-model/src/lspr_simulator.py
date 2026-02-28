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
