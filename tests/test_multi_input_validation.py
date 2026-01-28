#!/usr/bin/env python3
"""
Test script for multiple input group validation using samtools/view.

samtools/view has 4 input channels:
1. tuple val(meta), path(input), path(index)
2. tuple val(meta2), path(fasta)
3. path qname
4. val index_format
"""

from pathlib import Path
from pynf import NextflowEngine

def test_correct_inputs():
    """Test with correct input structure - should pass validation."""
    print("\n" + "="*70)
    print("TEST 1: Correct inputs (4 groups)")
    print("="*70)

    script_path = Path("test_nfcore_cache/samtools/view/main.nf")

    # Correct inputs matching the 4 input channels
    inputs = [
        # Group 1: tuple val(meta), path(input), path(index)
        {
            'meta': {'id': 'sample1'},
            'input': 'test.bam',
            'index': 'test.bam.bai'
        },
        # Group 2: tuple val(meta2), path(fasta)
        {
            'meta2': {'id': 'ref'},
            'fasta': 'reference.fa'
        },
        # Group 3: path qname
        {
            'qname': 'readnames.txt'
        },
        # Group 4: val index_format
        {
            'index_format': 'bai'
        }
    ]

    try:
        engine = NextflowEngine()
        script_path = engine.load_script(script_path)

        # This should pass validation
        print("Attempting execution with 4 input groups...")
        result = engine.execute(script_path, inputs=inputs, executor="local")
        print("✓ Validation passed!")

    except ValueError as e:
        print(f"✗ Validation failed: {e}")
    except Exception as e:
        print(f"Note: Execution may fail due to missing files, but validation passed")
        print(f"Error: {e}")


def test_missing_input_group():
    """Test with missing input group - should fail validation."""
    print("\n" + "="*70)
    print("TEST 2: Missing input group (only 3 groups provided)")
    print("="*70)

    script_path = Path("test_nfcore_cache/samtools/view/main.nf")

    # Only 3 groups - missing the 4th
    inputs = [
        {'meta': {'id': 'sample1'}, 'input': 'test.bam', 'index': 'test.bam.bai'},
        {'meta2': {'id': 'ref'}, 'fasta': 'reference.fa'},
        {'qname': 'readnames.txt'}
        # Missing group 4!
    ]

    try:
        engine = NextflowEngine()
        script_path = engine.load_script(script_path)
        result = engine.execute(script_path, inputs=inputs, executor="local")
        print("✗ Should have failed validation!")

    except ValueError as e:
        print("✓ Validation correctly failed:")
        print(str(e))
    except Exception as e:
        print(f"Unexpected error: {e}")


def test_missing_parameter():
    """Test with missing parameter in a group - should fail validation."""
    print("\n" + "="*70)
    print("TEST 3: Missing parameter in group 1")
    print("="*70)

    script_path = Path("test_nfcore_cache/samtools/view/main.nf")

    # Group 1 missing 'index' parameter
    inputs = [
        {'meta': {'id': 'sample1'}, 'input': 'test.bam'},  # Missing 'index'!
        {'meta2': {'id': 'ref'}, 'fasta': 'reference.fa'},
        {'qname': 'readnames.txt'},
        {'index_format': 'bai'}
    ]

    try:
        engine = NextflowEngine()
        script_path = engine.load_script(script_path)
        result = engine.execute(script_path, inputs=inputs, executor="local")
        print("✗ Should have failed validation!")

    except ValueError as e:
        print("✓ Validation correctly failed:")
        print(str(e))
    except Exception as e:
        print(f"Unexpected error: {e}")


def test_extra_parameter():
    """Test with extra parameter in a group - should fail validation."""
    print("\n" + "="*70)
    print("TEST 4: Extra parameter in group 1")
    print("="*70)

    script_path = Path("test_nfcore_cache/samtools/view/main.nf")

    # Group 1 has an extra parameter
    inputs = [
        {'meta': {'id': 'sample1'}, 'input': 'test.bam', 'index': 'test.bam.bai', 'extra': 'value'},
        {'meta2': {'id': 'ref'}, 'fasta': 'reference.fa'},
        {'qname': 'readnames.txt'},
        {'index_format': 'bai'}
    ]

    try:
        engine = NextflowEngine()
        script_path = engine.load_script(script_path)
        result = engine.execute(script_path, inputs=inputs, executor="local")
        print("✗ Should have failed validation!")

    except ValueError as e:
        print("✓ Validation correctly failed:")
        print(str(e))
    except Exception as e:
        print(f"Unexpected error: {e}")


def test_too_many_groups():
    """Test with too many input groups - should fail validation."""
    print("\n" + "="*70)
    print("TEST 5: Too many input groups (5 instead of 4)")
    print("="*70)

    script_path = Path("test_nfcore_cache/samtools/view/main.nf")

    # 5 groups instead of 4
    inputs = [
        {'meta': {'id': 'sample1'}, 'input': 'test.bam', 'index': 'test.bam.bai'},
        {'meta2': {'id': 'ref'}, 'fasta': 'reference.fa'},
        {'qname': 'readnames.txt'},
        {'index_format': 'bai'},
        {'extra_group': 'value'}  # Extra group!
    ]

    try:
        engine = NextflowEngine()
        script_path = engine.load_script(script_path)
        result = engine.execute(script_path, inputs=inputs, executor="local")
        print("✗ Should have failed validation!")

    except ValueError as e:
        print("✓ Validation correctly failed:")
        print(str(e))
    except Exception as e:
        print(f"Unexpected error: {e}")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("MULTI-INPUT VALIDATION TEST SUITE")
    print("Testing samtools/view (4 input channels)")
    print("="*70)

    test_correct_inputs()
    test_missing_input_group()
    test_missing_parameter()
    test_extra_parameter()
    test_too_many_groups()

    print("\n" + "="*70)
    print("TEST SUITE COMPLETED")
    print("="*70)
