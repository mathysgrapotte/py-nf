"""
Test script for AST extraction functionality.
"""

from pynf.tools import get_ast
from pynf.ast import print_ast, export_ast

# Test with existing Nextflow script
nf_file = "nextflow_scripts/simple-process.nf"

print("=" * 60)
print(f"Testing AST extraction on: {nf_file}")
print("=" * 60)

# Extract AST
ast = get_ast(nf_file)

# Pretty print
print("\n--- AST Structure ---")
print_ast(ast, max_depth=5)

# Export to JSON
print("\n--- Exporting to JSON ---")
export_ast(ast, "examples/simple_process_ast.json")
print("✓ Exported to examples/simple_process_ast.json")

# Export to YAML
print("\n--- Exporting to YAML ---")
export_ast(ast, "examples/simple_process_ast.yaml")
print("✓ Exported to examples/simple_process_ast.yaml")

print("\n✓ Test completed successfully")
