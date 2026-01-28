#!/usr/bin/env python3
"""Test script to verify verbose mode shows debug output."""

from pathlib import Path
from pynf import NextflowEngine

def test_verbose_mode():
    """Test with verbose=True to see debug output."""
    print("\n" + "="*70)
    print("VERBOSE MODE TEST")
    print("="*70)

    script_path = Path("test_nfcore_cache/samtools/view/main.nf")

    inputs = [
        {'meta': {'id': 'sample1'}, 'input': 'test.bam', 'index': 'test.bam.bai'},
        {'meta2': {'id': 'ref'}, 'fasta': 'reference.fa'},
        {'qname': 'readnames.txt'},
        {'index_format': 'bai'}
    ]

    try:
        engine = NextflowEngine()
        script_path = engine.load_script(script_path)

        print("\nExecuting with verbose=True...")
        print("="*70)
        result = engine.execute(script_path, inputs=inputs, executor="local", verbose=True)
        print("="*70)
        print("\n✓ Execution completed (you should see DEBUG messages above)")

    except Exception as e:
        print(f"Note: Execution failed but should have shown DEBUG output: {e}")

if __name__ == "__main__":
    test_verbose_mode()
