"""
Test the AST-based input parser in engine.py
"""

from pathlib import Path
from pynf import NextflowEngine

# Initialize engine
engine = NextflowEngine()

# Test with samtools/view
script_path = Path("nf-core-modules/samtools/view/main.nf")

print("=" * 80)
print("TESTING AST-BASED INPUT PARSER")
print("=" * 80)

# Test the new _parse_inputs_from_ast method
input_channels = engine._parse_inputs_from_ast(script_path)

print(f"\nFound {len(input_channels)} input channels:")
print()

for i, channel in enumerate(input_channels):
    print(f"Channel {i}:")
    print(f"  Type: {channel['type']}")
    print(f"  Parameters:")
    for param in channel['params']:
        print(f"    - {param['type']}({param['name']})")
    print()

print("=" * 80)
print("EXPECTED OUTPUT")
print("=" * 80)
print("""
Channel 0: tuple
  - val(meta)
  - path(input)
  - path(index)

Channel 1: tuple
  - val(meta2)
  - path(fasta)

Channel 2: path
  - path(qname)

Channel 3: val
  - val(index_format)
""")

print("=" * 80)
print("TEST COMPLETE")
print("=" * 80)
