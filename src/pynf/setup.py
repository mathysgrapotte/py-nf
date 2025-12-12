"""Auto-setup module for downloading Nextflow JAR.

This module provides automatic download and caching of the Nextflow fat JAR,
eliminating manual setup requirements and path issues when using pynf
from different directories.
"""

from __future__ import annotations

import urllib.request
from pathlib import Path

DEFAULT_VERSION = "25.10.2"
DOWNLOAD_URL_TEMPLATE = "https://www.nextflow.io/releases/v{version}/nextflow-{version}-one.jar"


def get_pynf_home() -> Path:
    """Return ~/.pynf/ directory, creating if needed.

    Returns:
        Path to the pynf home directory.
    """
    pynf_home = Path.home() / ".pynf"
    pynf_home.mkdir(exist_ok=True)
    return pynf_home


def get_jar_path(version: str = DEFAULT_VERSION) -> Path:
    """Return expected path to JAR file.

    Args:
        version: Nextflow version string (e.g., "25.10.2").

    Returns:
        Path where the JAR should be located.
    """
    return get_pynf_home() / f"nextflow-{version}-one.jar"


def download_nextflow_jar(version: str = DEFAULT_VERSION, force: bool = False) -> Path:
    """Download pre-built Nextflow JAR from nextflow.io.

    Args:
        version: Nextflow version to download (e.g., "25.10.2").
        force: Force re-download even if JAR already exists.

    Returns:
        Path to the downloaded JAR file.

    Raises:
        RuntimeError: If download fails.
    """
    jar_path = get_jar_path(version)

    if jar_path.exists() and not force:
        return jar_path

    url = DOWNLOAD_URL_TEMPLATE.format(version=version)

    print(f"Downloading Nextflow {version}...")
    print(f"  URL: {url}")
    print(f"  Destination: {jar_path}")

    def report_progress(block_num: int, block_size: int, total_size: int) -> None:
        downloaded = block_num * block_size
        if total_size > 0:
            percent = min(100, downloaded * 100 // total_size)
            mb_downloaded = downloaded / (1024 * 1024)
            mb_total = total_size / (1024 * 1024)
            print(
                f"\r  Progress: {percent}% ({mb_downloaded:.1f}/{mb_total:.1f} MB)",
                end="",
                flush=True,
            )

    try:
        urllib.request.urlretrieve(url, jar_path, reporthook=report_progress)
        print()  # Newline after progress
        print("  Download complete!")
        return jar_path
    except Exception as e:
        # Clean up partial download
        if jar_path.exists():
            jar_path.unlink()
        raise RuntimeError(f"Failed to download Nextflow JAR: {e}") from e


def ensure_nextflow_ready(version: str = DEFAULT_VERSION) -> Path:
    """Ensure Nextflow JAR is available, downloading if needed.

    This is the main entry point for auto-setup. Call this function
    before using NextflowEngine to ensure the JAR is available.

    Args:
        version: Nextflow version to use.

    Returns:
        Path to the JAR file.
    """
    jar_path = get_jar_path(version)

    if jar_path.exists():
        return jar_path

    return download_nextflow_jar(version)
