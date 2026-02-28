"""
Quick test of the new API endpoints
"""

import requests
import json
import time

BASE_URL = "http://localhost:8001"

print("=" * 60)
print("Quick API Endpoint Test")
print("=" * 60)

# Test 1: Health check
print("\n1. Health Check")
try:
    response = requests.get(f"{BASE_URL}/health", timeout=5)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
except Exception as e:
    print(f"   Error: {e}")
    exit(1)

# Test 2: Configure fast profile
print("\n2. Configure Fast Profile")
config = {
    "profile_type": "fast",
    "max_delta_n": 0.01,
    "time_param": 60.0,
    "noise_level": 0.02
}
try:
    response = requests.post(f"{BASE_URL}/spectrum/configure", json=config, timeout=5)
    print(f"   Status: {response.status_code}")
    data = response.json()
    print(f"   Profile: {data['config']['profile_type']}")
    print(f"   Max Δn: {data['config']['max_delta_n']}")
except Exception as e:
    print(f"   Error: {e}")

# Test 3: Get batch
print("\n3. Get Batch (10 spectra)")
try:
    response = requests.get(f"{BASE_URL}/spectrum/batch?count=10", timeout=10)
    print(f"   Status: {response.status_code}")
    data = response.json()
    print(f"   Count: {data['count']}")
    if data['spectra']:
        first = data['spectra'][0]
        last = data['spectra'][-1]
        print(f"   First peak: {first['peak_wavelength']:.2f} nm")
        print(f"   Last peak: {last['peak_wavelength']:.2f} nm")
        print(f"   Peak shift: {last['peak_wavelength'] - first['peak_wavelength']:.2f} nm")
except Exception as e:
    print(f"   Error: {e}")

# Test 4: Stream for 3 seconds
print("\n4. Stream Test (3 seconds)")
try:
    response = requests.get(f"{BASE_URL}/spectrum/stream", stream=True, timeout=5)
    print(f"   Status: {response.status_code}")
    
    start_time = time.time()
    count = 0
    first_peak = None
    last_peak = None
    
    for line in response.iter_lines():
        if line:
            decoded = line.decode('utf-8')
            if decoded.startswith('data: '):
                count += 1
                json_data = decoded[6:]
                spectrum = json.loads(json_data)
                
                if first_peak is None:
                    first_peak = spectrum['peak_wavelength']
                last_peak = spectrum['peak_wavelength']
        
        if time.time() - start_time > 3:
            break
    
    print(f"   Received: {count} spectra")
    if first_peak and last_peak:
        print(f"   Peak shift: {last_peak - first_peak:.3f} nm")

except requests.exceptions.Timeout:
    print("   Stream completed (timeout)")
except Exception as e:
    print(f"   Error: {e}")

print("\n" + "=" * 60)
print("✓ All tests completed!")
print("=" * 60)
