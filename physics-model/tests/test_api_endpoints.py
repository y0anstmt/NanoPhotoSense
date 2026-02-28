"""
Test script for new FastAPI endpoints
Tests SSE streaming, batch generation, and configuration
"""

import requests
import json
import time
from sseclient import SSEClient  # pip install sseclient-py

BASE_URL = "http://localhost:8001"


def test_health():
    """Test health endpoint"""
    print("\n=== Testing Health Endpoint ===")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")


def test_configure_slow():
    """Test configuration with slow infiltration profile"""
    print("\n=== Testing Configuration (Slow Profile) ===")
    
    config = {
        "profile_type": "slow",
        "max_delta_n": 0.005,
        "time_param": 3600.0,  # 1 hour
        "noise_level": 0.02,
        "base_peak": 520.0,
        "sensitivity_k": 200.0
    }
    
    response = requests.post(f"{BASE_URL}/spectrum/configure", json=config)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")


def test_configure_fast():
    """Test configuration with fast infiltration profile"""
    print("\n=== Testing Configuration (Fast Profile) ===")
    
    config = {
        "profile_type": "fast",
        "max_delta_n": 0.012,
        "time_param": 90.0,  # 90 seconds
        "noise_level": 0.03,
        "base_peak": 520.0,
        "sensitivity_k": 200.0
    }
    
    response = requests.post(f"{BASE_URL}/spectrum/configure", json=config)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")


def test_batch_spectra():
    """Test batch spectrum generation"""
    print("\n=== Testing Batch Spectrum Generation ===")
    
    response = requests.get(f"{BASE_URL}/spectrum/batch?count=10&sensor_id=LSPR-TEST")
    print(f"Status: {response.status_code}")
    
    data = response.json()
    print(f"Spectra count: {data['count']}")
    print(f"Generated at: {data['generated_at']}")
    
    # Show first and last spectrum
    if data['spectra']:
        first = data['spectra'][0]
        last = data['spectra'][-1]
        
        print(f"\nFirst spectrum:")
        print(f"  - Sensor ID: {first['sensor_id']}")
        print(f"  - Peak: {first['peak_wavelength']:.2f} nm")
        print(f"  - Δn: {first['delta_n']:.6f}")
        print(f"  - n: {first['refractive_index']:.6f}")
        
        print(f"\nLast spectrum:")
        print(f"  - Sensor ID: {last['sensor_id']}")
        print(f"  - Peak: {last['peak_wavelength']:.2f} nm")
        print(f"  - Δn: {last['delta_n']:.6f}")
        print(f"  - n: {last['refractive_index']:.6f}")
        
        print(f"\nPeak shift: {last['peak_wavelength'] - first['peak_wavelength']:.2f} nm")


def test_stream_spectra(duration_seconds=5):
    """Test SSE streaming (requires sseclient-py)"""
    print(f"\n=== Testing SSE Stream (for {duration_seconds} seconds) ===")
    
    try:
        url = f"{BASE_URL}/spectrum/stream?sensor_id=LSPR-STREAM"
        
        print(f"Connecting to {url}...")
        messages = SSEClient(url)
        
        start_time = time.time()
        count = 0
        first_spectrum = None
        last_spectrum = None
        
        for msg in messages:
            if msg.data:
                count += 1
                spectrum = json.loads(msg.data)
                
                if first_spectrum is None:
                    first_spectrum = spectrum
                last_spectrum = spectrum
                
                print(f"\nSpectrum #{count}:")
                print(f"  - Timestamp: {spectrum['timestamp']}")
                print(f"  - Peak: {spectrum['peak_wavelength']:.2f} nm")
                print(f"  - Δn: {spectrum['delta_n']:.6f}")
                print(f"  - n: {spectrum['refractive_index']:.6f}")
            
            # Stop after duration
            if time.time() - start_time > duration_seconds:
                break
        
        print(f"\n--- Stream Summary ---")
        print(f"Total spectra received: {count}")
        if first_spectrum and last_spectrum:
            print(f"Peak shift: {last_spectrum['peak_wavelength'] - first_spectrum['peak_wavelength']:.2f} nm")
            print(f"Δn change: {last_spectrum['delta_n'] - first_spectrum['delta_n']:.6f}")
    
    except Exception as e:
        print(f"Error: {e}")
        print("Note: Install sseclient-py with: pip install sseclient-py")


def test_stream_without_library(duration_seconds=5):
    """Test SSE streaming without external library"""
    print(f"\n=== Testing SSE Stream (Raw) for {duration_seconds} seconds ===")
    
    try:
        url = f"{BASE_URL}/spectrum/stream?sensor_id=LSPR-RAW"
        
        response = requests.get(url, stream=True, timeout=duration_seconds + 1)
        
        start_time = time.time()
        count = 0
        
        for line in response.iter_lines():
            if line:
                decoded = line.decode('utf-8')
                if decoded.startswith('data: '):
                    count += 1
                    json_data = decoded[6:]  # Remove 'data: ' prefix
                    spectrum = json.loads(json_data)
                    
                    print(f"\nSpectrum #{count}:")
                    print(f"  - Peak: {spectrum['peak_wavelength']:.2f} nm")
                    print(f"  - Δn: {spectrum['delta_n']:.6f}")
            
            # Stop after duration
            if time.time() - start_time > duration_seconds:
                break
        
        print(f"\nTotal spectra received: {count}")
    
    except requests.exceptions.Timeout:
        print("Stream completed (timeout reached)")
    except Exception as e:
        print(f"Error: {e}")


def main():
    """Run all tests"""
    print("=" * 60)
    print("FastAPI Endpoint Testing Suite")
    print("=" * 60)
    print("\nMake sure the API server is running:")
    print("  python src/api.py")
    print("  or: uvicorn api:app --reload --port 8001")
    print("=" * 60)
    
    try:
        # Test health
        test_health()
        
        # Configure fast profile
        test_configure_fast()
        
        # Test batch generation
        test_batch_spectra()
        
        # Test streaming (raw method, no dependencies)
        test_stream_without_library(duration_seconds=3)
        
        # Optionally test with sseclient if available
        # test_stream_spectra(duration_seconds=5)
        
        print("\n" + "=" * 60)
        print("All tests completed!")
        print("=" * 60)
    
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to API server")
        print("Make sure the server is running on port 8001")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
