# API Endpoints Documentation

## New Streaming Endpoints

### 1. GET `/spectrum/stream` - Server-Sent Events (SSE)

Streams spectrum data in real-time at 500ms intervals.

**Query Parameters:**
- `sensor_id` (optional): Sensor identifier (default: "LSPR-01")

**Response:** SSE stream with JSON data every 500ms

**JSON Schema:**
```json
{
  "sensor_id": "LSPR-01",
  "timestamp": 1700000000,
  "peak_wavelength": 645.2,
  "wavelengths": [400.0, 401.0, ...],
  "intensities": [0.01, 0.02, ...],
  "refractive_index": 1.333,
  "delta_n": 0.002
}
```

**Usage Examples:**

**cURL:**
```bash
curl -N http://localhost:8001/spectrum/stream?sensor_id=LSPR-01
```

**Python (with sseclient):**
```python
from sseclient import SSEClient

url = "http://localhost:8001/spectrum/stream?sensor_id=LSPR-01"
messages = SSEClient(url)

for msg in messages:
    if msg.data:
        spectrum = json.loads(msg.data)
        print(f"Peak: {spectrum['peak_wavelength']:.2f} nm")
```

**JavaScript (Browser):**
```javascript
const eventSource = new EventSource('http://localhost:8001/spectrum/stream?sensor_id=LSPR-01');

eventSource.onmessage = (event) => {
    const spectrum = JSON.parse(event.data);
    console.log(`Peak: ${spectrum.peak_wavelength} nm, Δn: ${spectrum.delta_n}`);
};

// Close connection
eventSource.close();
```

**Python (requests with streaming):**
```python
import requests
import json

response = requests.get(
    "http://localhost:8001/spectrum/stream?sensor_id=LSPR-01",
    stream=True
)

for line in response.iter_lines():
    if line:
        decoded = line.decode('utf-8')
        if decoded.startswith('data: '):
            json_data = decoded[6:]
            spectrum = json.loads(json_data)
            print(f"Peak: {spectrum['peak_wavelength']:.2f} nm")
```

---

### 2. GET `/spectrum/batch` - Batch Generation

Generates a batch of spectra for AI training/testing.

**Query Parameters:**
- `count` (optional): Number of spectra (1-10000, default: 100)
- `sensor_id` (optional): Sensor identifier (default: "LSPR-01")

**Response:**
```json
{
  "spectra": [
    {
      "sensor_id": "LSPR-01",
      "timestamp": 1700000000,
      "peak_wavelength": 520.2,
      "wavelengths": [400.0, 401.0, ...],
      "intensities": [0.01, 0.02, ...],
      "refractive_index": 1.330,
      "delta_n": 0.000
    },
    ...
  ],
  "count": 100,
  "generated_at": 1700000000
}
```

**Usage Examples:**

**cURL:**
```bash
curl "http://localhost:8001/spectrum/batch?count=100&sensor_id=LSPR-01"
```

**Python:**
```python
import requests

response = requests.get(
    "http://localhost:8001/spectrum/batch",
    params={"count": 100, "sensor_id": "LSPR-01"}
)

data = response.json()
print(f"Generated {data['count']} spectra")

# Extract peaks for analysis
peaks = [s['peak_wavelength'] for s in data['spectra']]
delta_ns = [s['delta_n'] for s in data['spectra']]
```

**Python (for ML training):**
```python
import numpy as np
import requests

# Get batch of spectra
response = requests.get(
    "http://localhost:8001/spectrum/batch?count=1000"
)
data = response.json()

# Convert to numpy arrays for training
X = np.array([s['intensities'] for s in data['spectra']])
y = np.array([s['delta_n'] for s in data['spectra']])

print(f"Training data shape: {X.shape}")
print(f"Labels shape: {y.shape}")
```

---

### 3. POST `/spectrum/configure` - Configure Infiltration Profile

Changes the active infiltration profile for streaming and batch endpoints.

**Request Body:**
```json
{
  "profile_type": "fast",
  "max_delta_n": 0.012,
  "time_param": 90.0,
  "noise_level": 0.03,
  "base_peak": 520.0,
  "sensitivity_k": 200.0
}
```

**Parameters:**
- `profile_type` (required): "slow", "fast", or "none"
- `max_delta_n` (optional): Maximum refractive index change (default: 0.01)
- `time_param` (optional): Time parameter - T for slow (seconds), τ for fast (seconds) (default: 60.0)
- `noise_level` (optional): Gaussian noise σ (default: 0.02)
- `base_peak` (optional): Base peak wavelength in nm (default: 520.0)
- `sensitivity_k` (optional): LSPR sensitivity in nm/RIU (default: 200.0)

**Response:**
```json
{
  "status": "Configuration updated successfully",
  "config": {
    "profile_type": "fast",
    "max_delta_n": 0.012,
    "time_param": 90.0,
    "noise_level": 0.03,
    "base_peak": 520.0,
    "sensitivity_k": 200.0
  },
  "timestamp": "2026-02-28T12:00:00"
}
```

**Usage Examples:**

**cURL (Slow Profile):**
```bash
curl -X POST "http://localhost:8001/spectrum/configure" \
  -H "Content-Type: application/json" \
  -d '{
    "profile_type": "slow",
    "max_delta_n": 0.005,
    "time_param": 3600.0,
    "noise_level": 0.02
  }'
```

**cURL (Fast Profile):**
```bash
curl -X POST "http://localhost:8001/spectrum/configure" \
  -H "Content-Type: application/json" \
  -d '{
    "profile_type": "fast",
    "max_delta_n": 0.012,
    "time_param": 90.0,
    "noise_level": 0.03
  }'
```

**cURL (No Infiltration):**
```bash
curl -X POST "http://localhost:8001/spectrum/configure" \
  -H "Content-Type: application/json" \
  -d '{
    "profile_type": "none",
    "noise_level": 0.01
  }'
```

**Python:**
```python
import requests

# Configure fast infiltration
config = {
    "profile_type": "fast",
    "max_delta_n": 0.012,
    "time_param": 90.0,
    "noise_level": 0.03,
    "base_peak": 520.0,
    "sensitivity_k": 200.0
}

response = requests.post(
    "http://localhost:8001/spectrum/configure",
    json=config
)

print(response.json())
```

---

## Complete Workflow Examples

### Example 1: Real-time Monitoring with Fast Infiltration

```python
import requests
import json
from sseclient import SSEClient

# 1. Configure fast infiltration
config = {
    "profile_type": "fast",
    "max_delta_n": 0.015,
    "time_param": 60.0,  # 1 minute time constant
    "noise_level": 0.02
}
requests.post("http://localhost:8001/spectrum/configure", json=config)

# 2. Start streaming
url = "http://localhost:8001/spectrum/stream?sensor_id=MONITOR-01"
messages = SSEClient(url)

# 3. Monitor in real-time
for msg in messages:
    if msg.data:
        spectrum = json.loads(msg.data)
        
        # Alert on significant change
        if spectrum['delta_n'] > 0.01:
            print(f"⚠️ ALERT: Δn = {spectrum['delta_n']:.4f}")
        else:
            print(f"✓ Normal: Δn = {spectrum['delta_n']:.4f}")
```

### Example 2: Generate Training Dataset

```python
import requests
import numpy as np
import pandas as pd

# 1. Configure slow infiltration
config = {
    "profile_type": "slow",
    "max_delta_n": 0.01,
    "time_param": 7200.0,  # 2 hours
    "noise_level": 0.03
}
requests.post("http://localhost:8001/spectrum/configure", json=config)

# 2. Generate large batch
response = requests.get(
    "http://localhost:8001/spectrum/batch?count=5000"
)
data = response.json()

# 3. Create training dataset
df = pd.DataFrame([
    {
        'peak_wavelength': s['peak_wavelength'],
        'refractive_index': s['refractive_index'],
        'delta_n': s['delta_n'],
        'intensities': s['intensities']
    }
    for s in data['spectra']
])

print(f"Dataset shape: {df.shape}")
df.to_csv('training_data.csv', index=False)
```

### Example 3: Switch Profiles Dynamically

```python
import requests
import time

def configure_profile(profile_type, **kwargs):
    config = {"profile_type": profile_type, **kwargs}
    response = requests.post(
        "http://localhost:8001/spectrum/configure",
        json=config
    )
    print(f"Configured: {profile_type}")
    return response.json()

# Simulate different scenarios
scenarios = [
    ("none", {}),
    ("slow", {"max_delta_n": 0.005, "time_param": 3600}),
    ("fast", {"max_delta_n": 0.02, "time_param": 30}),
]

for profile_type, params in scenarios:
    configure_profile(profile_type, **params)
    
    # Generate batch for this scenario
    response = requests.get(
        "http://localhost:8001/spectrum/batch?count=50"
    )
    data = response.json()
    
    print(f"  Generated {data['count']} spectra")
    time.sleep(1)
```

---

## JSON Schema Details

### SpectrumStreamData

All endpoints return data in this format:

```typescript
interface SpectrumStreamData {
  sensor_id: string;          // Sensor identifier (e.g., "LSPR-01")
  timestamp: number;          // Unix timestamp in seconds
  peak_wavelength: number;    // Peak wavelength in nm
  wavelengths: number[];      // Array of wavelength values (nm), typically 300 points
  intensities: number[];      // Array of intensity values, same length as wavelengths
  refractive_index: number;   // Current refractive index
  delta_n: number;           // Change in refractive index (Δn)
}
```

**Field Descriptions:**
- `sensor_id`: Unique sensor identifier
- `timestamp`: Unix timestamp (seconds since epoch)
- `peak_wavelength`: LSPR peak position in nm (e.g., 520-525 nm for Au)
- `wavelengths`: Wavelength array, default 400-700 nm in 1 nm steps
- `intensities`: Normalized intensity values (0-1 range)
- `refractive_index`: Absolute refractive index (e.g., 1.33 for water)
- `delta_n`: Change from baseline (1.33), indicates contamination level

---

## Profile Types

### Slow Linear Infiltration
- **Formula:** Δn(t) = max_delta_n × (t / T)
- **Use:** Gradual contamination over hours
- **time_param:** Total duration T in seconds

### Fast Exponential Infiltration
- **Formula:** Δn(t) = max_delta_n × (1 - e^(-t/τ))
- **Use:** Rapid contamination over minutes
- **time_param:** Time constant τ in seconds

### None
- **Formula:** Δn(t) = 0
- **Use:** Baseline measurements without infiltration

---

## Integration with Java Backend

```java
// Example RestClient for Quarkus
@Path("/api/lspr")
@RegisterRestClient(configKey = "physics-api")
public interface PhysicsAPIClient {
    
    @GET
    @Path("/spectrum/batch")
    BatchSpectrumResponse getBatch(
        @QueryParam("count") int count,
        @QueryParam("sensor_id") String sensorId
    );
    
    @POST
    @Path("/spectrum/configure")
    ConfigureResponse configure(InfiltrationConfig config);
}
```

---

## Testing

Run the test suite:
```bash
python tests/test_api_endpoints.py
```

Or test individual endpoints:
```bash
# Health check
curl http://localhost:8001/health

# Configure
curl -X POST http://localhost:8001/spectrum/configure \
  -H "Content-Type: application/json" \
  -d '{"profile_type": "fast", "max_delta_n": 0.01, "time_param": 60}'

# Get batch
curl "http://localhost:8001/spectrum/batch?count=10"

# Stream (CTRL+C to stop)
curl -N http://localhost:8001/spectrum/stream
```

---

## API Documentation

Interactive API documentation available at:
- **Swagger UI:** http://localhost:8001/docs
- **ReDoc:** http://localhost:8001/redoc
