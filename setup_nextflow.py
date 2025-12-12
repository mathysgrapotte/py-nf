#!/usr/bin/env python3
"""
Setup script for downloading Nextflow for py-nf.

This script downloads the pre-built Nextflow fat JAR from the official
Nextflow releases. The JAR is stored in ~/.pynf/ for use across all projects.

Usage:
    python setup_nextflow.py [--force] [--version VERSION]

Options:
    --force     Force re-download even if JAR already exists
    --version   Specify Nextflow version to download (e.g., 25.10.2)

Note: This script now downloads pre-built JARs instead of building from source.
      The JAR is automatically downloaded when using pynf, so this script is
      optional - it's useful for pre-downloading in offline environments.
"""

import argparse
import sys


def main() -> None:
    """Main entry point for setup script."""
    # Import here to avoid circular imports and to fail gracefully if pynf not installed
    try:
        from pynf.setup import (
            DEFAULT_VERSION,
            download_nextflow_jar,
            get_jar_path,
        )
    except ImportError:
        print("Error: pynf package not found.")
        print("Install with: pip install -e .")
        sys.exit(1)

    parser = argparse.ArgumentParser(
        description="Download Nextflow JAR for py-nf",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-download even if JAR already exists",
    )
    parser.add_argument(
        "--version",
        type=str,
        default=DEFAULT_VERSION,
        help=f"Nextflow version to download (default: {DEFAULT_VERSION})",
    )

    args = parser.parse_args()

    print(f"\nNextflow Setup for py-nf")
    print(f"{'='*50}\n")

    # Check if JAR already exists
    jar_path = get_jar_path(args.version)
    if jar_path.exists() and not args.force:
        print(f"Nextflow {args.version} already downloaded!")
        print(f"  Location: {jar_path}")
        print(f"\nUse --force to re-download.")
        sys.exit(0)

    # Download the JAR
    try:
        jar_path = download_nextflow_jar(version=args.version, force=args.force)
        print(f"\n{'='*50}")
        print(f"Setup complete!")
        print(f"{'='*50}")
        print(f"\nJAR location: {jar_path}")
        print(f"\nYou can now use pynf:")
        print(f"  from pynf import run_module")
        print(f'  result = run_module("script.nf")')
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
