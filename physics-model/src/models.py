"""
Pydantic data models for API request/response schemas
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime


class SimulatorConfig(BaseModel):
    """Configuration for LSPR simulator"""

    particle_radius: float = Field(default=40.0, ge=10.0, le=200.0, description="Particle radius (nm)")
    baseline_peak: float = Field(default=520.0, ge=400.0, le=800.0, description="Baseline peak wavelength (nm)")
    sensitivity: float = Field(default=60.0, ge=10.0, le=200.0, description="Sensitivity (nm/RIU)")


class SpectrumRequest(BaseModel):
    """Request to generate a single spectrum"""

    refractive_index: float = Field(..., ge=1.0, le=2.0, description="Medium refractive index")
    noise_level: float = Field(default=0.02, ge=0.0, le=0.5, description="Noise level")
    simulator_config: Optional[SimulatorConfig] = None

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "refractive_index": 1.34,
            "noise_level": 0.02
        }
    })


class SpectrumResponse(BaseModel):
    """Response containing spectrum data"""

    wavelengths: List[float] = Field(..., description="Wavelength array (nm)")
    intensities: List[float] = Field(..., description="Intensity array")
    peak_wavelength: float = Field(..., description="Detected peak wavelength (nm)")
    delta_n: float = Field(..., description="Refractive index change")
    risk_score: float = Field(..., description="Risk score (0-100)")


class TimeSeriesRequest(BaseModel):
    """Request to generate time series of readings"""

    sensor_id: str = Field(..., min_length=1, max_length=255, description="Sensor identifier")
    start_time: datetime = Field(default_factory=datetime.utcnow, description="Start timestamp")
    duration_hours: float = Field(default=24.0, ge=0.1, le=720.0, description="Duration (hours)")
    interval_minutes: float = Field(default=5.0, ge=0.1, le=60.0, description="Sampling interval (minutes)")
    contamination_rate: float = Field(default=0.0, ge=0.0, le=0.1, description="Contamination rate (RIU/hour)")
    simulator_config: Optional[SimulatorConfig] = None

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "sensor_id": "SENSOR-001",
            "duration_hours": 24.0,
            "interval_minutes": 5.0,
            "contamination_rate": 0.001
        }
    })


class ContaminationEventRequest(BaseModel):
    """Request to generate contamination event scenario"""

    sensor_id: str = Field(..., min_length=1, max_length=255, description="Sensor identifier")
    start_time: datetime = Field(default_factory=datetime.utcnow, description="Start timestamp")
    event_start_hour: float = Field(default=12.0, ge=0.0, description="Event start (hours from start)")
    event_duration_hours: float = Field(default=6.0, ge=0.1, le=100.0, description="Event duration (hours)")
    contamination_magnitude: float = Field(default=0.05, ge=0.0, le=0.5, description="Maximum Δn")
    total_duration_hours: float = Field(default=48.0, ge=1.0, le=720.0, description="Total duration (hours)")
    interval_minutes: float = Field(default=5.0, ge=0.1, le=60.0, description="Sampling interval (minutes)")
    simulator_config: Optional[SimulatorConfig] = None

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "sensor_id": "SENSOR-001",
            "event_start_hour": 12.0,
            "event_duration_hours": 6.0,
            "contamination_magnitude": 0.05
        }
    })


class SpectralReading(BaseModel):
    """Single spectral reading data point"""

    sensor_id: str
    timestamp: str
    peak_wavelength: float
    intensities: str
    refractive_index: float
    delta_n: float
    risk_score: float


class TimeSeriesResponse(BaseModel):
    """Response containing time series data"""

    readings: List[SpectralReading]
    count: int
    summary: dict = Field(default_factory=dict, description="Statistical summary")


class HealthResponse(BaseModel):
    """Health check response"""

    status: str
    timestamp: datetime
    version: str = "0.1.0"
