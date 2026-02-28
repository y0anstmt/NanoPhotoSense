"""
Example showcasing the JSON output format from the new API endpoints
"""

import requests
import json

BASE_URL = "http://localhost:8001"

print("=" * 80)
print("JSON Output Examples for New API Endpoints")
print("=" * 80)

# Configure the system
print("\n1. Configure Endpoint - Request:")
print("-" * 80)
config_request = {
    "profile_type": "fast",
    "max_delta_n": 0.012,
    "time_param": 90.0,
    "noise_level": 0.03,
    "base_peak": 520.0,
    "sensitivity_k": 200.0
}
print(json.dumps(config_request, indent=2))

print("\n1. Configure Endpoint - Response:")
print("-" * 80)
response = requests.post(f"{BASE_URL}/spectrum/configure", json=config_request)
print(json.dumps(response.json(), indent=2))

# Get a single spectrum from batch
print("\n\n2. Batch Endpoint - Single Spectrum Example:")
print("-" * 80)
response = requests.get(f"{BASE_URL}/spectrum/batch?count=1&sensor_id=LSPR-01")
data = response.json()

# Show just the first spectrum in full detail
if data['spectra']:
    spectrum = data['spectra'][0]
    # Truncate arrays for display
    spectrum_display = spectrum.copy()
    spectrum_display['wavelengths'] = spectrum['wavelengths'][:5] + ['...'] + spectrum['wavelengths'][-2:]
    spectrum_display['intensities'] = [round(x, 4) for x in spectrum['intensities'][:5]] + ['...'] + [round(x, 4) for x in spectrum['intensities'][-2:]]
    
    print(json.dumps(spectrum_display, indent=2))

# Show full batch response structure
print("\n\n3. Batch Endpoint - Full Response Structure:")
print("-" * 80)
response = requests.get(f"{BASE_URL}/spectrum/batch?count=3&sensor_id=LSPR-01")
data = response.json()

# Simplify for display
data_display = {
    "spectra": [
        {
            "sensor_id": s["sensor_id"],
            "timestamp": s["timestamp"],
            "peak_wavelength": round(s["peak_wavelength"], 2),
            "wavelengths": f"[{len(s['wavelengths'])} values: 400.0 to 700.0 nm]",
            "intensities": f"[{len(s['intensities'])} values]",
            "refractive_index": round(s["refractive_index"], 6),
            "delta_n": round(s["delta_n"], 6)
        }
        for s in data['spectra']
    ],
    "count": data["count"],
    "generated_at": data["generated_at"]
}
print(json.dumps(data_display, indent=2))

# Stream endpoint format
print("\n\n4. Stream Endpoint - SSE Format:")
print("-" * 80)
print("Event-stream format (text/event-stream):\n")

response = requests.get(f"{BASE_URL}/spectrum/stream?sensor_id=LSPR-01", stream=True, timeout=2)

count = 0
for line in response.iter_lines():
    if line:
        decoded = line.decode('utf-8')
        if decoded.startswith('data: '):
            count += 1
            if count == 1:  # Show first event
                json_data = decoded[6:]
                spectrum = json.loads(json_data)
                
                # Format for display
                spectrum_display = spectrum.copy()
                spectrum_display['wavelengths'] = spectrum['wavelengths'][:3] + ['...'] + spectrum['wavelengths'][-2:]
                spectrum_display['intensities'] = [round(x, 4) for x in spectrum['intensities'][:3]] + ['...'] + [round(x, 4) for x in spectrum['intensities'][-2:]]
                
                print("data: " + json.dumps(spectrum_display, indent=2))
                print("")  # SSE requires blank line
                
            if count >= 2:  # Stop after showing one
                break

print("\n(Stream continues every 500ms...)")

print("\n\n" + "=" * 80)
print("Complete JSON Schema Example")
print("=" * 80)

schema_example = {
    "sensor_id": "LSPR-01",
    "timestamp": 1700000000,
    "peak_wavelength": 645.2,
    "wavelengths": [400.0, 401.0, 402.0, "...", 699.0, 700.0],
    "intensities": [0.01, 0.02, 0.03, "...", 0.02, 0.01],
    "refractive_index": 1.333,
    "delta_n": 0.002
}

print("\nSpectrumStreamData Schema:")
print(json.dumps(schema_example, indent=2))

print("\n" + "=" * 80)
print("Field Descriptions:")
print("=" * 80)
print("""
sensor_id         : Sensor identifier (string)
timestamp         : Unix timestamp in seconds (integer)
peak_wavelength   : LSPR peak position in nm (float)
wavelengths       : Array of wavelength values, typically 400-700 nm (float[])
intensities       : Normalized intensity values 0-1 (float[])
refractive_index  : Absolute refractive index (float)
delta_n           : Change from baseline (Δn), indicates contamination (float)
""")

print("\n" + "=" * 80)
