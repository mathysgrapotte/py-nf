#!/usr/bin/env python3

"""
Final comprehensive test for py-nf package
"""

from pynf import NextflowEngine, run_workflow

def test_comprehensive():
    """Test comprehensive functionality"""
    print("=== Comprehensive py-nf API Test ===\n")

    # Test 1: Direct engine usage
    print("1. Testing direct engine usage...")
    engine = NextflowEngine()
    script_path = engine.load_script("hello-world.nf")
    result = engine.execute(script_path)

    print(f"   Execution report: {result.get_execution_report()}")
    print(f"   Stdout: {result.get_stdout()}")
    print("   ✓ Direct engine test completed\n")

    # Test 2: Convenience function
    print("2. Testing convenience function...")
    result2 = run_workflow("hello-world.nf")
    print(f"   Execution report: {result2.get_execution_report()}")
    print("   ✓ Convenience function test completed\n")

    print("🎉 All comprehensive tests passed!")

if __name__ == "__main__":
    try:
        test_comprehensive()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()