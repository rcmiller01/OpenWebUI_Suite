#!/usr/bin/env python3
"""
Quick test script for the FastVLM sidecar.
Run this to test the basic functionality.
"""

import asyncio
import httpx
import os

async def test_health():
    """Test the health endpoint"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://localhost:8115/healthz")
            print(f"Health check: {response.status_code}")
            print(f"Response: {response.json()}")
        except Exception as e:
            print(f"Health check failed: {e}")


async def test_image_url():
    """Test image analysis with URL"""
    async with httpx.AsyncClient() as client:
        try:
            payload = {
                "image_url": "https://upload.wikimedia.org/wikipedia/"
                             "commons/3/3f/Fronalpstock_big.jpg",
                "prompt": "Briefly describe the scene and any notable risks."
            }
            response = await client.post("http://localhost:8115/analyze",
                                         json=payload)
            print(f"Image URL test: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"Observations: {len(result.get('observations', []))}")
                if result.get('observations'):
                    obs_text = result['observations'][0]['text'][:200]
                    print(f"First observation: {obs_text}...")
        except Exception as e:
            print(f"Image URL test failed: {e}")


async def main():
    print("Testing FastVLM Sidecar...")
    print("=" * 50)

    # Check environment variables
    model = os.getenv("FASTVLM_MODEL", "apple/fastvlm-2.7b")
    device = os.getenv("DEVICE", "cuda")
    print(f"Model: {model}")
    print(f"Device: {device}")

    await test_health()
    print()

    # Only test image if service is running
    try:
        await test_image_url()
    except Exception as e:
        print(f"Image test skipped: {e}")

    print("\nTest complete!")

if __name__ == "__main__":
    asyncio.run(main())
