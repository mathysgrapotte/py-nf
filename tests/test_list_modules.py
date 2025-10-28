"""Test script for list_available_modules and list_submodules functions."""

from pathlib import Path
from pynf.nfcore import NFCoreModuleManager

# Create a temporary cache directory for testing
cache_dir = Path("./nf_core_list_cache")

# Initialize manager
manager = NFCoreModuleManager(cache_dir=cache_dir)

print("=" * 60)
print("Testing list_available_modules()...")
print("=" * 60)

try:
    modules = manager.list_available_modules()
    print(f"\n✓ Successfully fetched {len(modules)} top-level modules")
    print("\nFirst 10 modules:")
    for module in modules[:10]:
        print(f"  - {module}")

    if len(modules) > 10:
        print(f"  ... and {len(modules) - 10} more")

    # Verify cache file was created
    cache_file = cache_dir / "modules_list.txt"
    if cache_file.exists():
        print(f"\n✓ Cache file created: {cache_file}")

    # Test cache by calling again
    print("\nFetching again (should use cache)...")
    modules_cached = manager.list_available_modules()
    print(f"✓ Cached list has {len(modules_cached)} modules")

    if modules == modules_cached:
        print("✓ Cache works correctly (same results)")
    else:
        print("✗ Cache mismatch!")

except Exception as e:
    print(f"✗ Error: {e}")

print("\n" + "=" * 60)
print("Testing list_submodules()...")
print("=" * 60)

try:
    # Test with a module that likely has submodules
    test_module = "samtools"
    print(f"\nFetching submodules for '{test_module}'...")
    submodules = manager.list_submodules(test_module)

    if submodules:
        print(f"✓ Found {len(submodules)} submodules in '{test_module}':")
        for sub in submodules[:10]:
            print(f"  - {test_module}/{sub}")
        if len(submodules) > 10:
            print(f"  ... and {len(submodules) - 10} more")
    else:
        print(f"✗ No submodules found for '{test_module}'")

except Exception as e:
    print(f"✗ Error: {e}")
