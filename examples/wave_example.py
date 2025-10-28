#!/usr/bin/env python3
"""
Wave Client Example

This example demonstrates how to use the WaveClient to request containers
on-the-fly from Seqera Wave.

Prerequisites:
- Optional: TOWER_ACCESS_TOKEN for authenticated Wave requests

Usage:
    # Run all examples
    python examples/wave_example.py

    # Run specific example
    python examples/wave_example.py conda
    python examples/wave_example.py augment
    python examples/wave_example.py dockerfile
"""

import sys
import os
from pynf import WaveClient


def conda_build_example():
    """Example: Build container with bioinformatics tools via conda."""
    print("\n" + "=" * 70)
    print("Example 1: Build Container from Conda Packages")
    print("=" * 70)

    client = WaveClient()

    # Build container with bioinformatics tools
    result = client.build_from_conda(
        packages=["samtools=1.19", "bcftools=1.20"],
        channels=["conda-forge", "bioconda"],
        platform="linux/amd64",
    )

    if result["succeeded"]:
        print("✓ Container built successfully!")
        print(f"  Container URL: {result['container_url']}")
        if result.get("build_id"):
            print(f"  Build ID: {result['build_id']}")
    else:
        print(f"✗ Build failed: {result.get('error')}")


def augment_container_example():
    """Example: Augment existing container with additional tools."""
    print("\n" + "=" * 70)
    print("Example 2: Augment Existing Container")
    print("=" * 70)

    client = WaveClient()

    # Augment ubuntu with bioinformatics tools
    result = client.augment_container(
        base_image="ubuntu:22.04",
        conda_packages=["samtools", "bcftools", "bedtools"],
        conda_channels=["conda-forge", "bioconda"],
    )

    if result["succeeded"]:
        print("✓ Container augmented successfully!")
        print(f"  Container URL: {result['container_url']}")
    else:
        print(f"✗ Augmentation failed: {result.get('error')}")


def dockerfile_build_example():
    """Example: Build container from Dockerfile content."""
    print("\n" + "=" * 70)
    print("Example 3: Build from Dockerfile")
    print("=" * 70)

    # Note: This requires build_repository to be set
    if not os.getenv("WAVE_BUILD_REPOSITORY"):
        print("⚠️  Skipping Dockerfile example - WAVE_BUILD_REPOSITORY not set")
        print("   Set WAVE_BUILD_REPOSITORY='docker.io/youruser/repo' to enable")
        return

    client = WaveClient()

    # Dockerfile content
    dockerfile = """FROM ubuntu:22.04
RUN apt-get update && apt-get install -y \\
    samtools \\
    bcftools \\
    && rm -rf /var/lib/apt/lists/*
"""

    result = client.build_from_dockerfile(
        dockerfile_content=dockerfile,
        build_repository=os.getenv("WAVE_BUILD_REPOSITORY"),
        platform="linux/amd64",
    )

    if result["succeeded"]:
        print("✓ Container build initiated!")
        print(f"  Container URL: {result['container_url']}")
        print(f"  Build ID: {result['build_id']}")
        print(f"  Target Image: {result['target_image']}")
    else:
        print(f"✗ Build failed: {result.get('error')}")


def check_status_example():
    """Example: Check build status."""
    print("\n" + "=" * 70)
    print("Example 4: Check Build Status")
    print("=" * 70)

    if len(sys.argv) < 3:
        print(
            "⚠️  Provide build ID as argument: python examples/wave_example.py status <build_id>"
        )
        return

    build_id = sys.argv[2]
    client = WaveClient()

    print(f"Checking status for build: {build_id}")
    result = client.check_build_status(build_id=build_id, timeout=60)

    print(f"  Status: {result.get('status')}")
    print(f"  Succeeded: {result.get('succeeded')}")
    if result.get("duration"):
        print(f"  Duration: {result['duration']}")


def main():
    """Run Wave client examples."""
    print("\n🌊 Wave Client Examples")
    print("=" * 70)

    # Parse command line arguments
    if len(sys.argv) > 1:
        example = sys.argv[1].lower()
        if example == "conda":
            conda_build_example()
        elif example == "augment":
            augment_container_example()
        elif example == "dockerfile":
            dockerfile_build_example()
        elif example == "status":
            check_status_example()
        else:
            print(f"Unknown example: {example}")
            print("Available examples: conda, augment, dockerfile, status")
    else:
        # Run all examples
        try:
            conda_build_example()
            augment_container_example()
            dockerfile_build_example()
        except Exception as e:
            print(f"\n❌ Error running examples: {e}")
            import traceback

            traceback.print_exc()

    print("\n" + "=" * 70)
    print("✓ Examples completed!")
    print("=" * 70)


if __name__ == "__main__":
    main()
