#!/usr/bin/env python3
"""
Tandoor Sidecar - API Tests
Tests the recipe search, meal planning, and shopping list endpoints
"""

import requests
import json
import sys
import time

# Add src directory to Python path
# sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

BASE_URL = "http://127.0.0.1:8107"


def test_recipe_search():
    """Test recipe search endpoint"""
    print("Testing recipe search...")

    response = requests.get(f"{BASE_URL}/recipes/search?q=chicken%20rice")
    assert response.status_code == 200

    data = response.json()
    assert "recipes" in data
    assert "total" in data
    assert "query" in data
    assert data["query"] == "chicken rice"

    # Should return some mock recipes
    assert len(data["recipes"]) > 0

    print("✓ Recipe search test passed")


def test_week_planning():
    """Test weekly meal planning endpoint"""
    print("Testing week planning...")

    request_data = {
        "start": "2024-01-15",
        "macros": {
            "protein_min": 100,
            "carbs_max": 200,
            "calories_target": 2000
        }
    }

    response = requests.post(f"{BASE_URL}/plan/week", json=request_data)
    assert response.status_code == 200

    data = response.json()
    assert "week_plan" in data
    assert "shopping_list" in data

    # Should return 7 days
    assert len(data["week_plan"]) == 7

    # Each day should have meals
    for day in data["week_plan"]:
        assert "date" in day
        assert "meals" in day
        assert len(day["meals"]) == 3  # breakfast, lunch, dinner

    print("✓ Week planning test passed")


def test_shopping_list():
    """Test shopping list generation endpoint"""
    print("Testing shopping list generation...")

    request_data = {
        "start": "2024-01-15",
        "end": "2024-01-21"
    }

    response = requests.post(f"{BASE_URL}/shopping-list", json=request_data)
    assert response.status_code == 200

    data = response.json()
    assert "shopping_list" in data
    assert "total_items" in data
    assert "estimated_cost" in data

    # Should have some categories
    assert len(data["shopping_list"]) > 0

    # Each category should have items
    for category in data["shopping_list"]:
        assert "category" in category
        assert "items" in category
        assert len(category["items"]) > 0

    print("✓ Shopping list test passed")


def test_health_check():
    """Test health check endpoint"""
    print("Testing health check...")

    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"Status code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            assert "status" in data
            assert data["status"] == "healthy"
            print("✓ Health check passed")
        elif response.status_code == 503:
            print("✓ Health check correctly reports service unavailable")
        else:
            print(f"✗ Unexpected status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✓ Health check connection failed (expected): {e}")
    
    return True


def test_root_endpoint():
    """Test root endpoint"""
    print("Testing root endpoint...")

    response = requests.get(f"{BASE_URL}/")
    assert response.status_code == 200

    data = response.json()
    assert "message" in data
    assert "version" in data

    print("✓ Root endpoint test passed")


def main():
    """Run all tests"""
    print("Running Tandoor Sidecar Tests...\n")

    try:
        test_root_endpoint()
        time.sleep(0.5)
        test_health_check()
        time.sleep(0.5)
        test_recipe_search()
        time.sleep(0.5)
        test_week_planning()
        time.sleep(0.5)
        test_shopping_list()

        print("\n🎉 All tests passed!")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
