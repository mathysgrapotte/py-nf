#!/usr/bin/env python3
"""
Test script demonstrating the Nextflow native API for extracting input information
from nf-core modules using the NextflowEngine helper functions.
"""

import jpype
from pathlib import Path
from pynf import NextflowEngine

def test_native_api_input_extraction():
    """Test native API input extraction using NextflowEngine."""

    # Test with samtools/view module
    script_path = Path("test_nfcore_cache/samtools/view/main.nf")
    print(f"Testing with: {script_path}")
    print("=" * 70)

    # Create engine
    engine = NextflowEngine()

    # Set up Nextflow session
    Session = jpype.JClass("nextflow.Session")
    ScriptFile = jpype.JClass("nextflow.script.ScriptFile")
    ArrayList = jpype.JClass("java.util.ArrayList")

    session = Session()
    script_file = ScriptFile(jpype.java.nio.file.Paths.get(str(script_path)))
    session.init(script_file, ArrayList(), None, None)
    session.start()

    # Load and parse script
    loader = engine.ScriptLoaderFactory.create(session)
    java_path = jpype.java.nio.file.Paths.get(str(script_path))
    loader.parse(java_path)
    script = loader.getScript()

    print(f"✓ Script loaded: {script}")

    # Extract inputs using our helper functions
    print("\nExtracting inputs using native API...")
    inputs = engine._get_process_inputs(loader, script)

    # Display results
    print(f"\n✓ Found {len(inputs)} input channels:")
    print("=" * 70)

    for i, input_channel in enumerate(inputs):
        channel_type = input_channel['type']
        params = input_channel['params']

        print(f"\nInput Channel #{i + 1}: {channel_type}")
        print(f"  Parameters ({len(params)}):")
        for param in params:
            print(f"    - {param['type']}({param['name']})")

    # Cleanup
    session.destroy()

    print("\n" + "=" * 70)
    print("✓ Test completed successfully!")
    print("=" * 70)

if __name__ == "__main__":
    try:
        test_native_api_input_extraction()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
