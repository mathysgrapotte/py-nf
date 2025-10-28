"""
Manual test script for CLI functionality.

This script demonstrates how to use the pynf CLI and tools module.
Run with: uv run python tests/test_cli_manual.py
"""

from pathlib import Path
from pynf import tools

# Use a test cache directory to avoid cluttering the main cache
TEST_CACHE_DIR = Path("./test_nfcore_cache")
TEST_CACHE_DIR.mkdir(exist_ok=True)

print("=" * 70)
print("Testing pynf.tools functions")
print("=" * 70)

# Test 1: List modules
print("\n[TEST 1] Listing available modules...")
try:
    modules = tools.list_modules(cache_dir=TEST_CACHE_DIR)
    print(f"✓ Successfully listed {len(modules)} modules")
    print(f"  First 5 modules: {modules[:5]}")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 2: Check rate limit
print("\n[TEST 2] Checking GitHub API rate limit...")
try:
    status = tools.get_rate_limit_status()
    print(f"✓ Rate limit status retrieved")
    print(f"  Limit: {status['limit']}")
    print(f"  Remaining: {status['remaining']}")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 3: List submodules
print("\n[TEST 3] Listing submodules for 'samtools'...")
try:
    submodules = tools.list_submodules("samtools", cache_dir=TEST_CACHE_DIR)
    print(f"✓ Found {len(submodules)} submodules")
    print(f"  Submodules: {submodules[:5]}")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 4: Download a module
print("\n[TEST 4] Downloading 'fastqc' module...")
try:
    module = tools.download_module("fastqc", cache_dir=TEST_CACHE_DIR)
    print(f"✓ Module downloaded successfully")
    print(f"  Location: {module.local_path}")
    print(f"  main.nf exists: {module.main_nf.exists()}")
    print(f"  meta.yml exists: {module.meta_yml.exists()}")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 5: Check if module exists locally
print("\n[TEST 5] Checking if 'fastqc' exists locally...")
try:
    exists = tools.module_exists_locally("fastqc", cache_dir=TEST_CACHE_DIR)
    print(f"✓ Module exists locally: {exists}")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 6: Inspect a module
print("\n[TEST 6] Inspecting 'fastqc' module...")
try:
    info = tools.inspect_module("fastqc", cache_dir=TEST_CACHE_DIR)
    print(f"✓ Module inspected successfully")
    print(f"  Name: {info['name']}")
    print(f"  Path: {info['path']}")
    print(f"  main.nf lines: {info['main_nf_lines']}")
    print(f"  Meta keys: {list(info['meta'].keys()) if info['meta'] else 'None'}")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 7: Download a submodule
print("\n[TEST 7] Downloading 'samtools/view' submodule...")
try:
    module = tools.download_module("samtools/view", cache_dir=TEST_CACHE_DIR)
    print(f"✓ Submodule downloaded successfully")
    print(f"  Location: {module.local_path}")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 8: Get module inputs
print("\n[TEST 8] Getting input parameters from 'fastqc' module...")
try:
    inputs = tools.get_module_inputs("fastqc", cache_dir=TEST_CACHE_DIR)
    print(f"✓ Successfully retrieved input parameters")
    print(f"  Number of input groups: {len(inputs)}")
    for group_idx, group in enumerate(inputs):
        print(f"  Group {group_idx + 1} has {len(group)} parameters")
except Exception as e:
    print(f"✗ Error: {e}")

print("\n" + "=" * 70)
print("CLI Testing Instructions")
print("=" * 70)
print("""
To test the CLI after installation, run:

1. Install the package in editable mode:
   uv pip install -e .

2. Test individual commands:
   pynf list --limit 5
   pynf list-submodules samtools
   pynf download fastqc
   pynf inspect fastqc
   pynf list-inputs fastqc
   pynf list --rate-limit

3. Example with docker and metadata:
   pynf run fastqc --input sample.fastq --meta '{"id": "sample1"}' --docker

4. Get module inputs as JSON:
   pynf list-inputs fastqc --json

Note: The 'run' command requires a Nextflow environment setup.
""")

print("\n✓ All manual tests completed!")
