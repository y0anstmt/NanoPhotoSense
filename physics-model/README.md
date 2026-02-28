# NanoPhotoSense Physics Model

Python-based LSPR (Localized Surface Plasmon Resonance) physics simulator for nanoparticle-based water quality detection.

## Features

- **LSPR Simulation**: Physical modeling of gold nanoparticle optical response
- **Spectral Generation**: Time series generation with realistic temporal patterns
- **REST API**: FastAPI endpoints for integration with Java backend
- **Contamination Scenarios**: Simulate various contamination events

## Requirements

- Python 3.11+
- Dependencies: numpy, scipy, FastAPI, uvicorn, pydantic

## Installation

### Using pip

```bash
pip install -e .
```

### Using poetry (alternative)

```bash
poetry install
```

## Usage

### Start the API server

```bash
cd src
python api.py
```

Or with uvicorn directly:

```bash
uvicorn api:app --host 0.0.0.0 --port 8001 --reload
```

The API will be available at `http://localhost:8001`

### API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8001/docs`
- ReDoc: `http://localhost:8001/redoc`

### API Endpoints

#### Generate Single Spectrum

```bash
POST /api/spectrum
{
  "refractive_index": 1.34,
  "noise_level": 0.02
}
```

#### Generate Time Series

```bash
POST /api/timeseries
{
  "sensor_id": "SENSOR-001",
  "duration_hours": 24.0,
  "interval_minutes": 5.0,
  "contamination_rate": 0.001
}
```

#### Generate Contamination Event

```bash
POST /api/contamination-event
{
  "sensor_id": "SENSOR-001",
  "event_start_hour": 12.0,
  "event_duration_hours": 6.0,
  "contamination_magnitude": 0.05
}
```

#### NEW: Stream Spectra (SSE)

Real-time spectrum streaming at 500ms intervals:

```bash
GET /spectrum/stream?sensor_id=LSPR-01
```

#### NEW: Batch Generation

Generate batch of spectra for AI training:

```bash
GET /spectrum/batch?count=100&sensor_id=LSPR-01
```

#### NEW: Configure Infiltration Profile

Change infiltration profile at runtime:

```bash
POST /spectrum/configure
{
  "profile_type": "fast",
  "max_delta_n": 0.012,
  "time_param": 90.0,
  "noise_level": 0.03
}
```

See [API_ENDPOINTS.md](docs/API_ENDPOINTS.md) for detailed documentation.

## Docker

### Build image

```bash
docker build -t nanophotosense-physics:latest .
```

### Run container

```bash
docker run -p 8001:8001 nanophotosense-physics:latest
```

## Development

### Run tests

```bash
pytest tests/
```

### Code formatting

```bash
black src/
```

### Linting

```bash
ruff check src/
```

## Physics Model

### LSPR Theory

The simulator models the optical response of gold nanoparticles based on:

1. **Mie Theory**: Light scattering by spherical particles
2. **Refractive Index Sensitivity**: Peak wavelength shift proportional to medium refractive index
3. **Lorentzian Line Shape**: Characteristic LSPR absorption profile

### Key Parameters

- **Particle Radius**: 40 nm (typical for gold nanospheres)
- **Baseline Peak**: 520 nm (λmax in water)
- **Sensitivity**: 60 nm/RIU (refractive index unit)

### Infiltration Profiles

The simulator includes predefined infiltration profiles for modeling water contamination:

#### 1. **Slow Linear Infiltration**
- Formula: $\Delta n(t) = 0.001 \cdot t / T$
- Duration: Hours
- Use case: Gradual contamination monitoring

#### 2. **Fast Exponential Infiltration**
- Formula: $\Delta n(t) = 0.01 \cdot (1 - e^{-t/\tau})$
- Time constant: Minutes (τ ≈ 60s)
- Use case: Acute contamination events

#### 3. **Gaussian Noise**
- Formula: $I(\lambda) = I(\lambda) + \mathcal{N}(0, \sigma_{noise})$
- Models measurement uncertainty
- Typical σ: 0.01-0.05

For detailed documentation, see [infiltration_profiles.md](docs/infiltration_profiles.md).

Example usage:
```python
from lspr_simulator import create_infiltration_profile, generate_temporal_series, add_gaussian_noise

# Create fast infiltration
profile = create_infiltration_profile("fast", tau=90, max_delta_n=0.012)

# Generate temporal data
time, spectra, peaks = generate_temporal_series(600, 2000, profile)

# Add noise
noisy_spectra = add_gaussian_noise(spectra, sigma_noise=0.03)
```

### Risk Score Calculation

Risk score (0-100) based on refractive index deviation from baseline:
- Δn < 0.01: Low risk (< 50)
- Δn ≥ 0.01: Moderate risk (50-75)
- Δn ≥ 0.02: High risk (> 75)

## Architecture

```
src/
├── lspr_simulator.py    # Core physics engine
├── spectral_generator.py # Time series generation
├── api.py               # FastAPI REST endpoints
└── models.py            # Pydantic schemas
```

## Integration with Java Backend

The physics model runs as a microservice and communicates with the Quarkus backend via REST API.

Example Java integration:

```java
@RestClient
@RegisterRestClient(configKey = "physics-api")
public interface PhysicsModelClient {
    
    @POST
    @Path("/api/spectrum")
    SpectrumResponse generateSpectrum(SpectrumRequest request);
}
```

## License

MIT License

## Contact

NanoPhotoSense Project Team
