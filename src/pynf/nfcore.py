"""
nf-core module management for py-nf.

This module provides utilities to download and use nf-core modules
from the official nf-core/modules repository.
"""

import requests
from pathlib import Path
from typing import Optional


class NFCoreModule:
    """
    Represents an nf-core module with its files and metadata.
    """

    def __init__(self, tool_name: str, local_path: Path):
        self.tool_name = tool_name
        self.local_path = local_path
        self.main_nf = local_path / "main.nf"
        self.meta_yml = local_path / "meta.yml"

    def exists(self) -> bool:
        """Check if module files are downloaded."""
        return self.main_nf.exists() and self.meta_yml.exists()


class NFCoreModuleManager:
    """
    Manages downloading and caching nf-core modules.
    """

    GITHUB_BASE_URL = "https://raw.githubusercontent.com/nf-core/modules/master/modules/nf-core"

    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize the module manager.

        Args:
            cache_dir: Directory to cache downloaded modules.
                      Defaults to ./nf-core-modules/
        """
        self.cache_dir = cache_dir or Path("./nf-core-modules")
        self.cache_dir.mkdir(exist_ok=True)

    def download_module(self, tool_name: str, force: bool = False) -> NFCoreModule:
        """
        Download an nf-core module from GitHub.

        Args:
            tool_name: Name of the tool (e.g., 'fastqc', 'samtools/view')
            force: Force re-download even if cached

        Returns:
            NFCoreModule object with paths to downloaded files

        Raises:
            ValueError: If module doesn't exist or download fails

        Example:
            >>> manager = NFCoreModuleManager()
            >>> module = manager.download_module('fastqc')
            >>> print(module.main_nf)
            nf-core-modules/fastqc/main.nf
        """
        # Create local directory
        module_dir = self.cache_dir / tool_name
        module_dir.mkdir(parents=True, exist_ok=True)

        module = NFCoreModule(tool_name, module_dir)

        # Check if already cached
        if module.exists() and not force:
            print(f"Module {tool_name} already cached at {module_dir}")
            return module

        # Download main.nf
        print(f"Downloading {tool_name} module from nf-core...")
        main_nf_url = f"{self.GITHUB_BASE_URL}/{tool_name}/main.nf"
        self._download_file(main_nf_url, module.main_nf)

        # Download meta.yml
        meta_yml_url = f"{self.GITHUB_BASE_URL}/{tool_name}/meta.yml"
        self._download_file(meta_yml_url, module.meta_yml)

        print(f"Module downloaded successfully to {module_dir}")
        return module

    def _download_file(self, url: str, dest: Path):
        """
        Download a file from URL to destination.

        Args:
            url: Source URL
            dest: Destination file path

        Raises:
            ValueError: If download fails
        """
        response = requests.get(url)

        if response.status_code == 404:
            raise ValueError(f"Module file not found: {url}")

        response.raise_for_status()

        with open(dest, 'w') as f:
            f.write(response.text)

    def list_available_modules(self) -> list[str]:
        """
        List all available nf-core modules.

        This could use the GitHub API to list the modules directory.
        For now, returns an empty list (implement if needed).
        """
        # TODO: Use GitHub API to list modules
        # GET https://api.github.com/repos/nf-core/modules/contents/modules/nf-core
        return []


def download_nfcore_module(tool_name: str, cache_dir: Optional[Path] = None) -> NFCoreModule:
    """
    Convenience function to download an nf-core module.

    Args:
        tool_name: Name of the tool (e.g., 'fastqc')
        cache_dir: Optional cache directory

    Returns:
        NFCoreModule object

    Example:
        >>> from pynf.nfcore import download_nfcore_module
        >>> module = download_nfcore_module('fastqc')
        >>> print(module.main_nf)
    """
    manager = NFCoreModuleManager(cache_dir)
    return manager.download_module(tool_name)
