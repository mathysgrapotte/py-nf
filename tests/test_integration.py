#!/usr/bin/env python3

"""
Integration test for py-nf package
Tests running a simple Nextflow script from Python
"""

from pathlib import Path

from pynf import NextflowEngine, run_module

def test_basic_engine():
    """Test basic NextflowEngine functionality"""
    print("Testing NextflowEngine...")

    # Create engine instance
    engine = NextflowEngine()

    # Load the hello.nf script
    script_path = engine.load_script("nextflow/tests/hello.nf")
    print(f"Loaded script path: {script_path}")

    # Execute the script
    print("Executing script...")
    result = engine.execute(script_path)

    # Print results
    print(f"Execution report: {result.get_execution_report()}")
    print(f"Output files: {result.get_output_files()}")
    print(f"Stdout: {result.get_stdout()}")

    print("✓ Basic engine test completed")

def test_convenience_function():
    """Test the convenience run_module function"""
    print("\nTesting run_module convenience function...")

    # Use the one-liner
    result = run_module("nextflow/tests/hello.nf")

    # Print results
    print(f"Execution report: {result.get_execution_report()}")
    print(f"Output files: {result.get_output_files()}")

    print("✓ Convenience function test completed")


def test_file_output_process_outputs_output_txt():
    """Ensure file-output-process.nf publishes output.txt"""

    engine = NextflowEngine()
    script_path = engine.load_script("nextflow_scripts/file-output-process.nf")
    result = engine.execute(script_path)

    outputs = result.get_output_files()
    print(f"outputs: {outputs}")

    assert any(Path(path).name == "output.txt" for path in outputs), outputs

    print("✓ file-output-process produced output.txt")

if __name__ == "__main__":
    print("=== py-nf Integration Test ===\n")

    try:
        test_basic_engine()
        test_convenience_function()
        test_file_output_process_outputs_output_txt()
        print("\n🎉 All tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()