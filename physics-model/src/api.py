"""
FastAPI REST API for LSPR physics simulator
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import numpy as np
from typing import List

try:
    from models import (
        SpectrumRequest,
        SpectrumResponse,
        TimeSeriesRequest,
        TimeSeriesResponse,
        ContaminationEventRequest,
        SpectralReading,
        HealthResponse,
        SimulatorConfig,
    )
    from lspr_simulator import LSPRSimulator
    from spectral_generator import SpectralGenerator
except ImportError:
    from .models import (
        SpectrumRequest,
        SpectrumResponse,
        TimeSeriesRequest,
        TimeSeriesResponse,
        ContaminationEventRequest,
        SpectralReading,
        HealthResponse,
        SimulatorConfig,
    )
    from .lspr_simulator import LSPRSimulator
    from .spectral_generator import SpectralGenerator


app = FastAPI(
    title="NanoPhotoSense Physics API",
    description="LSPR-based nanoparticle detection physics simulator",
    version="0.1.0",
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def create_simulator(config: SimulatorConfig = None) -> LSPRSimulator:
    """Create simulator instance with optional config"""
    if config is None:
        return LSPRSimulator()
    return LSPRSimulator(
        particle_radius=config.particle_radius,
        baseline_peak=config.baseline_peak,
        sensitivity=config.sensitivity,
    )


@app.get("/", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(status="healthy", timestamp=datetime.utcnow())


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint"""
    return HealthResponse(status="healthy", timestamp=datetime.utcnow())


@app.post("/api/spectrum", response_model=SpectrumResponse)
async def generate_spectrum(request: SpectrumRequest):
    """
    Generate a single LSPR spectrum for given refractive index.

    Args:
        request: Spectrum generation parameters

    Returns:
        Spectrum data with peak analysis
    """
    try:
        simulator = create_simulator(request.simulator_config)

        # Generate spectrum
        wavelengths, intensities = simulator.generate_spectrum(
            refractive_index=request.refractive_index, noise_level=request.noise_level
        )

        # Detect peak
        peak_wavelength = simulator.detect_peak_wavelength(wavelengths, intensities)

        # Calculate metrics
        delta_n = simulator.calculate_delta_n(peak_wavelength)
        risk_score = simulator.calculate_risk_score(delta_n)

        return SpectrumResponse(
            wavelengths=wavelengths.tolist(),
            intensities=intensities.tolist(),
            peak_wavelength=float(peak_wavelength),
            delta_n=float(delta_n),
            risk_score=float(risk_score),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Spectrum generation failed: {str(e)}")


@app.post("/api/timeseries", response_model=TimeSeriesResponse)
async def generate_time_series(request: TimeSeriesRequest):
    """
    Generate time series of spectral readings.

    Args:
        request: Time series generation parameters

    Returns:
        List of spectral readings with summary statistics
    """
    try:
        simulator = create_simulator(request.simulator_config)
        generator = SpectralGenerator(
            simulator=simulator,
            base_refractive_index=1.33,
            contamination_rate=request.contamination_rate,
        )

        # Generate time series
        readings_data = generator.generate_time_series(
            sensor_id=request.sensor_id,
            start_time=request.start_time,
            duration_hours=request.duration_hours,
            interval_minutes=request.interval_minutes,
        )

        # Convert to Pydantic models
        readings = [SpectralReading(**data) for data in readings_data]

        # Calculate summary statistics
        risk_scores = [r.risk_score for r in readings]
        delta_ns = [r.delta_n for r in readings]

        summary = {
            "mean_risk_score": float(np.mean(risk_scores)),
            "max_risk_score": float(np.max(risk_scores)),
            "mean_delta_n": float(np.mean(delta_ns)),
            "max_delta_n": float(np.max(delta_ns)),
            "sensor_id": request.sensor_id,
            "duration_hours": request.duration_hours,
        }

        return TimeSeriesResponse(readings=readings, count=len(readings), summary=summary)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Time series generation failed: {str(e)}")


@app.post("/api/contamination-event", response_model=TimeSeriesResponse)
async def generate_contamination_event(request: ContaminationEventRequest):
    """
    Generate time series with specific contamination event scenario.

    Args:
        request: Contamination event parameters

    Returns:
        List of spectral readings showing contamination event
    """
    try:
        simulator = create_simulator(request.simulator_config)
        generator = SpectralGenerator(simulator=simulator, base_refractive_index=1.33)

        # Generate contamination event
        readings_data = generator.generate_contamination_event(
            sensor_id=request.sensor_id,
            start_time=request.start_time,
            event_start_hour=request.event_start_hour,
            event_duration_hours=request.event_duration_hours,
            contamination_magnitude=request.contamination_magnitude,
            total_duration_hours=request.total_duration_hours,
            interval_minutes=request.interval_minutes,
        )

        # Convert to Pydantic models
        readings = [SpectralReading(**data) for data in readings_data]

        # Calculate summary statistics
        risk_scores = [r.risk_score for r in readings]
        delta_ns = [r.delta_n for r in readings]

        summary = {
            "mean_risk_score": float(np.mean(risk_scores)),
            "max_risk_score": float(np.max(risk_scores)),
            "mean_delta_n": float(np.mean(delta_ns)),
            "max_delta_n": float(np.max(delta_ns)),
            "sensor_id": request.sensor_id,
            "event_start_hour": request.event_start_hour,
            "event_duration_hours": request.event_duration_hours,
            "contamination_magnitude": request.contamination_magnitude,
        }

        return TimeSeriesResponse(readings=readings, count=len(readings), summary=summary)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Contamination event generation failed: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
