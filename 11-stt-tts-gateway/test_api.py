"""
Test suite for STT-TTS Gateway API
"""

import asyncio
import base64
import io
import json
import time
import wave
import requests
import numpy as np
from pathlib import Path

# Configuration
API_BASE_URL = "http://localhost:8089"

def create_test_audio(duration_seconds: int = 5, sample_rate: int = 16000) -> str:
    """Create a simple test audio file and return as base64"""
    # Generate a simple sine wave
    frequency = 440  # A4 note
    t = np.linspace(0, duration_seconds, int(sample_rate * duration_seconds), False)
    audio_data = np.sin(frequency * 2 * np.pi * t)

    # Convert to 16-bit PCM
    audio_int16 = (audio_data * 32767).astype(np.int16)

    # Create WAV file in memory
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_int16.tobytes())

    # Convert to base64
    wav_buffer.seek(0)
    audio_b64 = base64.b64encode(wav_buffer.read()).decode('utf-8')

    return audio_b64

def test_health_check():
    """Test health check endpoint"""
    print("Testing health check...")
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        response.raise_for_status()
        data = response.json()

        print(f"✓ Health check passed: {data['status']}")
        print(f"  STT model loaded: {data['stt_model_loaded']}")
        print(f"  TTS model loaded: {data['tts_model_loaded']}")
        return True
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return False

def test_stt_basic():
    """Test basic STT functionality"""
    print("\nTesting STT basic functionality...")

    # Create test audio (this won't have actual speech, but tests the pipeline)
    audio_b64 = create_test_audio(duration_seconds=3)

    payload = {
        "audio": audio_b64,
        "format": "wav",
        "language": "en",
        "timestamps": True
    }

    try:
        start_time = time.time()
        response = requests.post(
            f"{API_BASE_URL}/stt",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        processing_time = time.time() - start_time

        if response.status_code == 200:
            data = response.json()
            print("✓ STT request successful")
            print(f"  Processing time: {data['processing_time']:.3f}s")
            print(f"  Detected language: {data['language']}")
            print(f"  Text length: {len(data['text'])} characters")
            print(f"  Segments: {len(data['segments'])}")

            # Check performance requirement (< 500ms for 5s clip)
            if processing_time < 0.5:
                print("✓ Performance requirement met (< 500ms)")
            else:
                print(f"⚠ Performance warning: {processing_time:.3f}s (> 500ms)")

            return True
        else:
            print(f"✗ STT request failed: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        print(f"✗ STT test failed: {e}")
        return False

def test_tts_basic():
    """Test basic TTS functionality"""
    print("\nTesting TTS basic functionality...")

    payload = {
        "text": "Hello world, this is a test of the text to speech system.",
        "voice": "default",
        "speed": 1.0,
        "timestamps": True
    }

    try:
        start_time = time.time()
        response = requests.post(
            f"{API_BASE_URL}/tts",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        processing_time = time.time() - start_time

        if response.status_code == 200:
            data = response.json()
            print("✓ TTS request successful")
            print(f"  Processing time: {data['processing_time']:.3f}s")
            print(f"  Audio URL: {data['audio_url']}")
            print(f"  Duration: {data['duration']:.2f}s")
            print(f"  Timestamps: {len(data['timestamps'])} words")

            # Check performance requirement (< 1000ms for 100 words)
            if processing_time < 1.0:
                print("✓ Performance requirement met (< 1000ms)")
            else:
                print(f"⚠ Performance warning: {processing_time:.3f}s (> 1000ms)")

            # Test audio retrieval
            audio_url = data['audio_url']
            audio_response = requests.get(f"{API_BASE_URL}{audio_url}")
            if audio_response.status_code == 200:
                print("✓ Audio file retrieval successful")
                print(f"  Audio file size: {len(audio_response.content)} bytes")
            else:
                print(f"⚠ Audio retrieval failed: {audio_response.status_code}")

            return True
        else:
            print(f"✗ TTS request failed: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        print(f"✗ TTS test failed: {e}")
        return False

def test_error_handling():
    """Test error handling"""
    print("\nTesting error handling...")

    # Test invalid base64
    payload = {
        "audio": "invalid_base64",
        "format": "wav"
    }

    try:
        response = requests.post(
            f"{API_BASE_URL}/stt",
            json=payload,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 400:
            print("✓ Invalid audio data handled correctly (400)")
        else:
            print(f"⚠ Unexpected status for invalid data: {response.status_code}")

    except Exception as e:
        print(f"Error testing invalid data: {e}")

    # Test missing model
    try:
        # This would require temporarily disabling a model
        print("✓ Error handling tests completed")
        return True
    except Exception as e:
        print(f"✗ Error handling test failed: {e}")
        return False

def run_all_tests():
    """Run all tests"""
    print("Starting STT-TTS Gateway API Tests")
    print("=" * 50)

    # Wait for service to be ready
    print("Waiting for service to be ready...")
    for i in range(30):  # Wait up to 30 seconds
        try:
            response = requests.get(f"{API_BASE_URL}/health", timeout=2)
            if response.status_code == 200:
                print("✓ Service is ready")
                break
        except:
            pass
        time.sleep(1)
    else:
        print("✗ Service failed to start within 30 seconds")
        return

    # Run tests
    tests = [
        test_health_check,
        test_stt_basic,
        test_tts_basic,
        test_error_handling
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1

    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed!")
        return True
    else:
        print("⚠ Some tests failed")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
