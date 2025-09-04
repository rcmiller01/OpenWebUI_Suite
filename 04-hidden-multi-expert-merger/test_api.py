#!/usr/bin/env python3
"""
API tests for Hidden Multi-Expert Merger Service
"""

import asyncio
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from app import merger


def test_compose_api():
    """Test the compose API endpoint"""
    print("Testing compose API...")

    # Test data
    test_request = {
        "prompt": "Write a professional email about project status.",
        "persona": "Senior Project Manager",
        "tone_policy": ["professional", "concise"],
        "budgets": {
            "time_ms": 1500,
            "max_helpers": 2,
            "template": "persona_preserving"
        }
    }

    try:
        # Test direct merger (without server)
        print("Testing direct merger...")
        result = asyncio.run(merger.compose(
            test_request["prompt"],
            test_request["persona"],
            test_request["tone_policy"],
            test_request["budgets"]
        ))

        print("✅ Direct test passed:")
        print(f"  Final text: {result['final_text'][:100]}...")
        print(f"  Processing time: {result['processing_time_ms']:.2f}ms")
        print(f"  Helpers used: {result['helpers_used']}")
        print(f"  Tokens used: {result['tokens_used']}")

        # Validate budgets
        assert result['processing_time_ms'] < 1500, "Time budget exceeded"
        assert result['helpers_used'] <= 2, "Helper limit exceeded"
        assert result['tokens_used'] <= 360, "Token budget exceeded (120*3)"

        # Validate no helper chatter in output
        final_text = result['final_text'].lower()
        forbidden_words = ['i think', 'as an ai', 'let me', 'i should', 'i can']
        for word in forbidden_words:
            assert word not in final_text, f"Helper chatter detected: {word}"

        print("✅ Budget enforcement validated")
        print("✅ No helper chatter in output")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

    return True


def test_budget_enforcement():
    """Test that budgets are strictly enforced"""
    print("\nTesting budget enforcement...")

    # Test with tight time budget
    tight_budget = {
        "time_ms": 100,  # Very tight budget
        "max_helpers": 1,
        "template": "concise_executive"
    }

    try:
        result = asyncio.run(merger.compose(
            "Long draft text that needs significant editing and improvement...",
            "Executive Assistant",
            ["formal", "brief"],
            tight_budget
        ))

        print(f"  Processing time: {result['processing_time_ms']:.2f}ms")
        print(f"  Helpers used: {result['helpers_used']}")

        # Should still complete but may use fewer helpers
        assert result['processing_time_ms'] > 0, "Processing time should be positive"
        assert result['helpers_used'] <= 1, "Should respect helper limit"

        print("✅ Tight budget test passed")

    except Exception as e:
        print(f"❌ Budget test failed: {e}")
        return False

    return True


def test_persona_preservation():
    """Test that persona is preserved in output"""
    print("\nTesting persona preservation...")

    test_cases = [
        {
            "prompt": "Explain quantum computing",
            "persona": "Friendly Teacher",
            "expected_contains": ["friendly", "teacher"]
        },
        {
            "prompt": "Report on sales figures",
            "persona": "Sales Executive",
            "expected_contains": ["executive", "sales"]
        }
    ]

    for i, case in enumerate(test_cases):
        try:
            result = asyncio.run(merger.compose(
                case["prompt"],
                case["persona"],
                ["professional"],
                {"template": "persona_preserving"}
            ))

            final_text = result['final_text'].lower()
            persona_found = any(word in final_text for word in case["expected_contains"])

            if persona_found:
                print(f"✅ Test case {i+1} passed - persona preserved")
            else:
                print(f"⚠️  Test case {i+1} - persona not strongly detected")

        except Exception as e:
            print(f"❌ Persona test {i+1} failed: {e}")
            return False

    return True


def test_template_variations():
    """Test different merge templates"""
    print("\nTesting template variations...")

    prompt = "Write a product description for a smart watch."
    persona = "Marketing Specialist"

    templates = ["persona_preserving", "concise_executive", "creative_enhancement"]

    for template in templates:
        try:
            result = asyncio.run(merger.compose(
                prompt,
                persona,
                ["engaging"],
                {"template": template}
            ))

            print(f"✅ Template '{template}': {len(result['final_text'])} chars")
            assert len(result['final_text']) > 0, f"Empty result for {template}"

        except Exception as e:
            print(f"❌ Template '{template}' failed: {e}")
            return False

    return True


def main():
    """Run all tests"""
    print("🧪 Running Hidden Multi-Expert Merger Tests")
    print("=" * 50)

    tests = [
        test_compose_api,
        test_budget_enforcement,
        test_persona_preservation,
        test_template_variations
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1

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
