"""
FastAPI REST API for LSPR physics simulator
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from datetime import datetime
import numpy as np
from typing import List
import asyncio
import json
import time

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
        SpectrumStreamData,
        BatchSpectrumResponse,
        InfiltrationConfig,
        ConfigureResponse,
    )
    from lspr_simulator import (
        LSPRSimulator,
        compute_lspr_spectrum,
        apply_refractive_index_shift,
        create_infiltration_profile,
        add_gaussian_noise,
    )
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
        SpectrumStreamData,
        BatchSpectrumResponse,
        InfiltrationConfig,
        ConfigureResponse,
    )
    from .lspr_simulator import (
        LSPRSimulator,
        compute_lspr_spectrum,
        apply_refractive_index_shift,
        create_infiltration_profile,
        add_gaussian_noise,
    )
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

# Global state for infiltration configuration
current_infiltration_config = InfiltrationConfig(
    profile_type="none",
    max_delta_n=0.0,
    time_param=60.0,
    noise_level=0.02,
    base_peak=520.0,
    sensitivity_k=200.0,
)

# Track simulation start time for temporal profiles
simulation_start_time = time.time()


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


def generate_spectrum_data(
    sensor_id: str = "LSPR-01",
    wavelengths: np.ndarray = None,
    config: InfiltrationConfig = None,
    elapsed_time: float = 0.0,
) -> SpectrumStreamData:
    """
    Generate a single spectrum based on current configuration.

    Args:
        sensor_id: Sensor identifier
        wavelengths: Wavelength array (if None, uses default 400-700nm)
        config: Infiltration configuration
        elapsed_time: Time elapsed since simulation start (seconds)

    Returns:
        SpectrumStreamData object
    """
    if wavelengths is None:
        wavelengths = np.linspace(400, 700, 300)

    if config is None:
        config = current_infiltration_config

    # Calculate current delta_n based on profile and elapsed time
    if config.profile_type == "slow":
        profile_func = create_infiltration_profile(
            "slow", T=config.time_param, max_delta_n=config.max_delta_n
        )
        delta_n = profile_func(elapsed_time)
    elif config.profile_type == "fast":
        profile_func = create_infiltration_profile(
            "fast", tau=config.time_param, max_delta_n=config.max_delta_n
        )
        delta_n = profile_func(elapsed_time)
    else:
        delta_n = 0.0  # No infiltration

    # Calculate shifted peak
    current_peak = apply_refractive_index_shift(
        config.base_peak, delta_n, config.sensitivity_k
    )

    # Generate spectrum
    peak_width = 40.0  # Standard LSPR peak width
    amplitude = 1.0
    intensities = compute_lspr_spectrum(wavelengths, current_peak, peak_width, amplitude)

    # Add noise
    if config.noise_level > 0:
        intensities = add_gaussian_noise(
            intensities.reshape(1, -1), config.noise_level, seed=None
        )[0]

    # Calculate refractive index
    baseline_n = 1.33  # Water baseline
    refractive_index = baseline_n + delta_n

    return SpectrumStreamData(
        sensor_id=sensor_id,
        timestamp=int(time.time()),
        peak_wavelength=float(current_peak),
        wavelengths=wavelengths.tolist(),
        intensities=intensities.tolist(),
        refractive_index=float(refractive_index),
        delta_n=float(delta_n),
    )


@app.get("/spectrum/stream")
async def stream_spectra(sensor_id: str = "LSPR-01"):
    """
    Server-Sent Events (SSE) endpoint that streams spectrum data every 500ms.

    Args:
        sensor_id: Sensor identifier (default: LSPR-01)

    Returns:
        SSE stream of JSON spectrum data

    Example:
        curl http://localhost:8001/spectrum/stream?sensor_id=LSPR-01
    """

    async def event_generator():
        """Generate SSE events with spectrum data"""
        global simulation_start_time
        simulation_start_time = time.time()  # Reset on new stream

        wavelengths = np.linspace(400, 700, 300)

        try:
            while True:
                # Calculate elapsed time
                elapsed = time.time() - simulation_start_time

                # Generate spectrum
                spectrum = generate_spectrum_data(
                    sensor_id=sensor_id,
                    wavelengths=wavelengths,
                    config=current_infiltration_config,
                    elapsed_time=elapsed,
                )

                # Format as SSE event
                json_data = spectrum.model_dump_json()
                yield f"data: {json_data}\n\n"

                # Wait 500ms before next emission
                await asyncio.sleep(0.5)

        except asyncio.CancelledError:
            # Client disconnected
            pass

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/spectrum/batch", response_model=BatchSpectrumResponse)
async def get_batch_spectra(count: int = 100, sensor_id: str = "LSPR-01"):
    """
    Generate a batch of spectra for AI training.

    Args:
        count: Number of spectra to generate (default: 100, max: 10000)
        sensor_id: Sensor identifier (default: LSPR-01)

    Returns:
        Array of spectrum data

    Example:
        GET /spectrum/batch?count=100&sensor_id=LSPR-01
    """
    if count < 1 or count > 10000:
        raise HTTPException(
            status_code=400, detail="Count must be between 1 and 10000"
        )

    try:
        wavelengths = np.linspace(400, 700, 300)
        spectra = []

        # Calculate time interval for the batch
        # Spread spectra across the profile duration
        if current_infiltration_config.profile_type != "none":
            max_time = current_infiltration_config.time_param * 2  # Cover 2x the characteristic time
        else:
            max_time = 3600.0  # 1 hour default

        time_interval = max_time / count

        for i in range(count):
            elapsed_time = i * time_interval

            spectrum = generate_spectrum_data(
                sensor_id=sensor_id,
                wavelengths=wavelengths,
                config=current_infiltration_config,
                elapsed_time=elapsed_time,
            )
            spectra.append(spectrum)

        return BatchSpectrumResponse(
            spectra=spectra,
            count=len(spectra),
            generated_at=int(time.time()),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Batch generation failed: {str(e)}"
        )


@app.post("/spectrum/configure", response_model=ConfigureResponse)
async def configure_infiltration(config: InfiltrationConfig):
    """
    Configure infiltration profile at runtime.

    Changes the active infiltration profile used by streaming and batch endpoints.

    Args:
        config: Infiltration configuration

    Returns:
        Confirmation with updated configuration

    Example:
        POST /spectrum/configure
        {
            "profile_type": "fast",
            "max_delta_n": 0.012,
            "time_param": 90.0,
            "noise_level": 0.03,
            "base_peak": 520.0,
            "sensitivity_k": 200.0
        }
    """
    global current_infiltration_config, simulation_start_time

    # Validate profile type
    if config.profile_type not in ["slow", "fast", "none"]:
        raise HTTPException(
            status_code=400,
            detail="profile_type must be 'slow', 'fast', or 'none'",
        )

    # Update global configuration
    current_infiltration_config = config

    # Reset simulation start time
    simulation_start_time = time.time()

    return ConfigureResponse(
        status="Configuration updated successfully",
        config=current_infiltration_config,
        timestamp=datetime.utcnow(),
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
