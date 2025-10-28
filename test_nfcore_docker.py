#!/usr/bin/env python3

"""
Test script for running nf-core modules with Docker containers.

This script demonstrates:
1. Downloading an nf-core module (FASTQC)
2. Running it with Docker enabled
3. Providing proper meta map parameters
4. Collecting outputs
"""

from pathlib import Path
from pynf import NextflowEngine
from pynf.nfcore import download_nfcore_module
import tempfile
import shutil


def create_test_fastq():
    """Create a minimal test FASTQ file."""
    test_dir = Path(tempfile.mkdtemp(prefix="pynf_test_"))
    fastq_file = test_dir / "test_sample.fastq"

    # Create a minimal FASTQ content (just a few reads)
    content = """@SEQ_ID_1
GATTTGGGGTTCAAAGCAGTATCGATCAAATAGTAAATCCATTTGTTCAACTCACAGTTT
+
!''*((((***+))%%%++)(%%%%).1***-+*''))**55CCF>>>>>>CCCCCCC65
@SEQ_ID_2
GATTTGGGGTTCAAAGCAGTATCGATCAAATAGTAAATCCATTTGTTCAACTCACAGTTT
+
!''*((((***+))%%%++)(%%%%).1***-+*''))**55CCF>>>>>>CCCCCCC65
"""

    # Write to file (uncompressed for simplicity)
    with open(fastq_file, 'w') as f:
        f.write(content)

    return test_dir, fastq_file


def test_fastqc_with_docker():
    """
    Test running FASTQC nf-core module with Docker.
    """
    print("=" * 70)
    print("TEST: Running nf-core FASTQC module with Docker")
    print("=" * 70)

    # Step 1: Download the nf-core FASTQC module
    print("\n[1/5] Downloading FASTQC module from nf-core...")
    module = download_nfcore_module('fastqc')
    print(f"    Module downloaded to: {module.local_path}")
    print(f"    Main script: {module.main_nf}")

    # Step 2: Create test input data
    print("\n[2/5] Creating test FASTQ file...")
    test_dir, fastq_file = create_test_fastq()
    print(f"    Test file: {fastq_file}")

    # Step 3: Prepare meta map
    print("\n[3/5] Preparing meta map...")
    meta = {
        'id': 'test_sample_001',
        'single_end': True
    }
    print(f"    Meta map: {meta}")

    # Step 4: Configure Docker
    print("\n[4/5] Configuring Docker...")
    docker_config = {
        'enabled': True,
        'remove': True,  # Auto-remove container after execution
    }
    print(f"    Docker config: {docker_config}")

    # Step 5: Execute the module
    print("\n[5/5] Executing FASTQC module...")
    engine = NextflowEngine()

    try:
        result = engine.execute(
            script_path=module.main_nf,
            executor='local',
            input_files=[str(fastq_file)],
            meta=meta,
            docker_config=docker_config
        )

        print("\n" + "=" * 70)
        print("RESULTS")
        print("=" * 70)

        # Display outputs
        print("\nOutput files generated:")
        output_files = result.get_output_files()
        for file_path in output_files:
            print(f"  - {file_path}")

        # Check for expected outputs
        html_files = [f for f in output_files if f.endswith('.html')]
        zip_files = [f for f in output_files if f.endswith('.zip')]

        print(f"\nHTML reports: {len(html_files)}")
        print(f"ZIP archives: {len(zip_files)}")

        # Display execution report
        print("\nExecution report:")
        report = result.get_execution_report()
        print(f"  Completed tasks: {report.get('completed_tasks', 'N/A')}")
        print(f"  Failed tasks: {report.get('failed_tasks', 'N/A')}")
        print(f"  Work directory: {report.get('work_dir', 'N/A')}")

        print("\n" + "=" * 70)
        print("TEST PASSED")
        print("=" * 70)

        return True

    except Exception as e:
        print("\n" + "=" * 70)
        print("TEST FAILED")
        print("=" * 70)
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Cleanup test files
        print("\nCleaning up test files...")
        shutil.rmtree(test_dir)


if __name__ == '__main__':
    # Run test
    print("Starting nf-core Docker integration test...\n")

    test_passed = test_fastqc_with_docker()

    print("\n\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"FASTQC test: {'PASSED' if test_passed else 'FAILED'}")
    print("=" * 70)
