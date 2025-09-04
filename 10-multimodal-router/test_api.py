#!/usr/bin/env python3
"""
Quick test script for the multimodal router.
Run this to test the basic functionality.
"""

import asyncio
import httpx
import os

async def test_health():
    """Test the health endpoint"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://localhost:8110/healthz")
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
            response = await client.post("http://localhost:8110/mm/image",
                                         json=payload)
            print(f"Image URL test: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"Observations: {len(result.get('observations', []))}")
                if result.get('observations'):
                    obs_text = result['observations'][0]['text'][:100]
                    print(f"First observation: {obs_text}...")
        except Exception as e:
            print(f"Image URL test failed: {e}")


async def main():
    print("Testing Multimodal Router...")
    print("=" * 50)

    # Check environment variables
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("⚠️  Warning: OPENROUTER_API_KEY not set")
    else:
        print("✅ OPENROUTER_API_KEY is set")

    vision_model = os.getenv("VISION_MODEL", "openai/gpt-4o-mini")
    print(f"Vision model: {vision_model}")

    await test_health()
    print()

    # Only test image if API key is available
    if api_key:
        await test_image_url()
    else:
        print("Skipping image test - no API key")

    print("\nTest complete!")

if __name__ == "__main__":
    asyncio.run(main())
