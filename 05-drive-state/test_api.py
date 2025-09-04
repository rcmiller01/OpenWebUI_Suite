#!/usr/bin/env python3
"""
API tests for Drive State Service
"""

import asyncio
import sys
import os
import time
import json

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from drive_state import drive_manager


def test_drive_state_creation():
    """Test drive state creation and initialization"""
    print("Testing drive state creation...")

    # Test new user creation
    user_id = "test_user_1"
    state = drive_manager.get_drive_state(user_id)

    print(f"  ✅ Created state for {user_id}")
    print(f"    Energy: {state.energy:.2f}")
    print(f"    Sociability: {state.sociability:.2f}")
    print(f"    Curiosity: {state.curiosity:.2f}")
    print(f"    Empathy: {state.empathy_reserve:.2f}")
    print(f"    Novelty: {state.novelty_seek:.2f}")

    # Verify all values are in [0..1] range
    assert 0.0 <= state.energy <= 1.0, f"Energy out of range: {state.energy}"
    assert 0.0 <= state.sociability <= 1.0, f"Sociability out of range: {state.sociability}"
    assert 0.0 <= state.curiosity <= 1.0, f"Curiosity out of range: {state.curiosity}"
    assert 0.0 <= state.empathy_reserve <= 1.0, f"Empathy out of range: {state.empathy_reserve}"
    assert 0.0 <= state.novelty_seek <= 1.0, f"Novelty out of range: {state.novelty_seek}"

    print("  ✅ All drive values in valid range")
    return True


def test_drive_updates():
    """Test drive state updates with deltas"""
    print("\nTesting drive updates...")

    user_id = "test_user_2"

    # Test positive delta
    deltas = {"energy": 0.2, "sociability": -0.1}
    state = drive_manager.update_drive_state(user_id, deltas, "Test positive update")

    print(f"  ✅ Applied deltas: {deltas}")
    print(f"    New energy: {state.energy:.2f} (should be ~0.7)")
    print(f"    New sociability: {state.sociability:.2f} (should be ~0.4)")

    # Verify changes (allow for random walk and clamping)
    assert state.energy >= 0.7, f"Energy should be at least 0.7: {state.energy}"
    assert abs(state.sociability - 0.4) < 0.15, f"Sociability not updated correctly: {state.sociability}"

    # Test clamping (try to exceed bounds)
    extreme_deltas = {"energy": 2.0, "curiosity": -2.0}
    state = drive_manager.update_drive_state(user_id, extreme_deltas, "Test clamping")

    print(f"  ✅ Applied extreme deltas: {extreme_deltas}")
    print(f"    Clamped energy: {state.energy:.2f} (should be 1.0)")
    print(f"    Clamped curiosity: {state.curiosity:.2f} (should be 0.0)")

    # Verify clamping
    assert state.energy == 1.0, f"Energy not clamped to 1.0: {state.energy}"
    assert state.curiosity == 0.0, f"Curiosity not clamped to 0.0: {state.curiosity}"

    print("  ✅ Clamping works correctly")
    return True


def test_time_decay():
    """Test time-based decay to baseline"""
    print("\nTesting time decay...")

    user_id = "test_user_3"

    # Set initial state away from baseline
    initial_deltas = {"energy": 0.8, "sociability": 0.2}
    state = drive_manager.update_drive_state(user_id, initial_deltas, "Set initial state")

    print(f"  Initial state - Energy: {state.energy:.2f}, Sociability: {state.sociability:.2f}")

    # Simulate time passage by directly modifying timestamp
    state.timestamp -= 100  # Go back 100 seconds
    drive_manager.save_states()

    # Get state again (should trigger decay)
    state = drive_manager.get_drive_state(user_id)

    print(f"  After decay - Energy: {state.energy:.2f}, Sociability: {state.sociability:.2f}")

    # Energy should have decayed toward 0.5
    assert state.energy < 0.8, f"Energy should decay: {state.energy}"
    assert state.sociability > 0.2, f"Sociability should decay: {state.sociability}"

    print("  ✅ Time decay working correctly")
    return True


def test_style_policy():
    """Test style policy generation"""
    print("\nTesting style policy generation...")

    user_id = "test_user_4"

    # Test high energy state
    high_energy_deltas = {"energy": 0.8, "sociability": 0.8}
    drive_manager.update_drive_state(user_id, high_energy_deltas, "High energy test")

    policy = drive_manager.get_style_policy(user_id)

    print(f"  High energy policy: {policy['energy_level']}")
    print(f"  Social style: {policy['social_style']}")
    print(f"  Style hints: {policy['style_hints']}")

    assert policy['energy_level'] == 'very_high', f"Expected very_high energy: {policy['energy_level']}"
    assert policy['social_style'] == 'very_high', f"Expected very_high sociability: {policy['social_style']}"
    assert len(policy['style_hints']) > 0, "Should have style hints"

    # Test low energy state
    low_energy_deltas = {"energy": -0.6, "curiosity": -0.6}
    drive_manager.update_drive_state(user_id, low_energy_deltas, "Low energy test")

    policy = drive_manager.get_style_policy(user_id)

    print(f"  Low energy policy: {policy['energy_level']}")
    print(f"  Curiosity level: {policy['curiosity_level']}")

    assert policy['energy_level'] == 'low', f"Expected low energy: {policy['energy_level']}"
    assert policy['curiosity_level'] == 'very_low', f"Expected very_low curiosity: {policy['curiosity_level']}"

    print("  ✅ Style policy generation working")
    return True


def test_persistence():
    """Test drive state persistence"""
    print("\nTesting persistence...")

    user_id = "test_user_5"

    # Set a specific state
    test_deltas = {"novelty_seek": 0.9, "empathy_reserve": 0.1}
    state1 = drive_manager.update_drive_state(user_id, test_deltas, "Persistence test")

    print(f"  Set state - Novelty: {state1.novelty_seek:.2f}, Empathy: {state1.empathy_reserve:.2f}")

    # Create new manager instance (simulates service restart)
    new_manager = drive_manager.__class__()
    state2 = new_manager.get_drive_state(user_id)

    print(f"  Loaded state - Novelty: {state2.novelty_seek:.2f}, Empathy: {state2.empathy_reserve:.2f}")

    # Should be approximately the same (allowing for random walk)
    assert abs(state1.novelty_seek - state2.novelty_seek) < 0.1, "Novelty not persisted"
    assert abs(state1.empathy_reserve - state2.empathy_reserve) < 0.1, "Empathy not persisted"

    print("  ✅ Persistence working correctly")
    return True


def test_scenario_long_tech_session():
    """Test scenario: Long tech session decreases sociability"""
    print("\nTesting scenario: Long tech session ↓ sociability")

    user_id = "tech_user"

    # Start with high sociability
    initial_state = drive_manager.update_drive_state(user_id, {"sociability": 0.8}, "Initial high sociability")

    print(f"  Initial sociability: {initial_state.sociability:.2f}")

    # Simulate long tech session (multiple updates)
    for i in range(5):
        drive_manager.update_drive_state(user_id, {"sociability": -0.1}, f"Tech session update {i+1}")
        time.sleep(0.1)  # Small delay

    final_state = drive_manager.get_drive_state(user_id)

    print(f"  Final sociability: {final_state.sociability:.2f}")

    # Sociability should have decreased (be lower than initial high value)
    assert final_state.sociability < 0.8, f"Sociability should decrease in long tech session: {final_state.sociability}"

    print("  ✅ Long tech session scenario working")
    return True


def test_scenario_user_sadness():
    """Test scenario: User sadness increases empathy"""
    print("\nTesting scenario: User sadness ↑ empathy")

    user_id = "sad_user"

    # Start with low empathy
    initial_state = drive_manager.update_drive_state(user_id, {"empathy_reserve": 0.2}, "Initial low empathy")

    print(f"  Initial empathy: {initial_state.empathy_reserve:.2f}")

    # Simulate sadness event
    sadness_update = drive_manager.update_drive_state(user_id, {"empathy_reserve": 0.4}, "User expressed sadness")

    print(f"  After sadness: {sadness_update.empathy_reserve:.2f}")

    # Empathy should have increased (be higher than initial low value)
    assert sadness_update.empathy_reserve > 0.5, f"Empathy should increase with sadness: {sadness_update.empathy_reserve}"

    print("  ✅ User sadness scenario working")
    return True


def main():
    """Run all tests"""
    print("🧪 Running Drive State Service Tests")
    print("=" * 50)

    tests = [
        test_drive_state_creation,
        test_drive_updates,
        test_time_decay,
        test_style_policy,
        test_persistence,
        test_scenario_long_tech_session,
        test_scenario_user_sadness
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")

    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} passed")

    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
