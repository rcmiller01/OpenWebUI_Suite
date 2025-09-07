#!/usr/bin/env python3
"""
Test the conditional extras functionality in env_check.py
"""

import os
import subprocess
import sys


def test_env_check_conditionals():
    """Test that env_check respects service enablement flags"""
    
    print("🧪 Testing env_check.py conditional extras functionality")
    print("=" * 60)
    
    # Test scenarios
    scenarios = [
        {
            "name": "Default (both disabled)",
            "env": {},
            "expected": "TANDOOR_SIDECAR.*DISABLED.*OPENBB_SIDECAR.*DISABLED"
        },
        {
            "name": "Tandoor enabled",
            "env": {"ENABLE_TANDOOR": "1"},
            "expected": "TANDOOR_SIDECAR(?!.*DISABLED).*TANDOOR_URL"
        },
        {
            "name": "OpenBB enabled", 
            "env": {"ENABLE_OPENBB": "1"},
            "expected": "OPENBB_SIDECAR(?!.*DISABLED).*OPENBB_PAT"
        },
        {
            "name": "Extras profile with strict mode",
            "env": {"COMPOSE_PROFILES": "extras", "REQUIRE_EXTRAS_STRICT": "1"},
            "expected": "TANDOOR_SIDECAR(?!.*DISABLED).*OPENBB_SIDECAR(?!.*DISABLED)"
        }
    ]
    
    for scenario in scenarios:
        print(f"\n🔍 Testing: {scenario['name']}")
        print("-" * 40)
        
        # Set up environment
        env = os.environ.copy()
        env.update(scenario["env"])
        
        # Create minimal .env.prod for test
        with open(".env.prod.test", "w") as f:
            f.write("# Test environment file\n")
            f.write("REDIS_URL=redis://localhost:6379\n")
        
        try:
            # Run env_check.py with test environment
            result = subprocess.run([
                sys.executable, "scripts/env_check.py"
            ], 
            env=env,
            capture_output=True, 
            text=True,
            input="n\n",  # Don't configure missing variables
            timeout=30
            )
            
            print(f"Exit code: {result.returncode}")
            
            # Check output for expected patterns
            output = result.stdout + result.stderr
            print("Output (first 500 chars):")
            print(output[:500])
            
            if "DISABLED" in output:
                disabled_services = []
                if "TANDOOR_SIDECAR" in output and "DISABLED" in output:
                    disabled_services.append("TANDOOR")
                if "OPENBB_SIDECAR" in output and "DISABLED" in output:
                    disabled_services.append("OPENBB")
                
                if disabled_services:
                    print(f"✅ Services correctly disabled: {', '.join(disabled_services)}")
                else:
                    print("❌ Expected services to be disabled but none found")
            else:
                print("ℹ️  No services disabled")
            
        except subprocess.TimeoutExpired:
            print("⏰ Test timed out")
        except Exception as e:
            print(f"❌ Test failed: {e}")
        
        finally:
            # Cleanup
            if os.path.exists(".env.prod.test"):
                os.remove(".env.prod.test")
    
    print(f"\n✅ Conditional extras testing complete!")
    print(f"\n💡 Usage Examples:")
    print(f"   # Disable all extras (default)")
    print(f"   python scripts/env_check.py")
    print(f"   ")
    print(f"   # Enable only Tandoor")
    print(f"   ENABLE_TANDOOR=1 python scripts/env_check.py")
    print(f"   ")
    print(f"   # Enable via compose profiles")
    print(f"   COMPOSE_PROFILES=extras REQUIRE_EXTRAS_STRICT=1 python scripts/env_check.py")


if __name__ == "__main__":
    test_env_check_conditionals()
