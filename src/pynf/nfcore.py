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

    def _fetch_modules_iterative(self) -> list[str]:
        """
        Iteratively fetch all nf-core modules from GitHub API with pagination.

        Uses a queue-based approach to traverse all directories.
        Paginate through results to minimize API requests (~15 instead of 1500+).

        Returns:
            List of available module names

        Raises:
            ValueError: If GitHub API request fails
        """
        modules = []
        queue = [
            ("https://api.github.com/repos/nf-core/modules/contents/modules/nf-core", "")
        ]

        while queue:
            url, prefix = queue.pop(0)
            page = 1

            while True:
                paginated_url = f"{url}?per_page=100&page={page}"

                try:
                    response = requests.get(paginated_url)
                    response.raise_for_status()
                except requests.RequestException as e:
                    raise ValueError(f"Failed to fetch modules from GitHub API: {e}")

                items = response.json()
                if not isinstance(items, list) or len(items) == 0:
                    break

                for item in items:
                    if item["type"] == "dir":
                        module_path = f"{prefix}{item['name']}" if prefix else item["name"]
                        modules.append(module_path)
                        subdir_url = item["url"]
                        queue.append((subdir_url, f"{module_path}/"))

                page += 1

        return sorted(modules)

    def list_available_modules(self) -> list[str]:
        """
        List all available nf-core modules.

        Returns cached list if available, otherwise fetches from GitHub
        and caches the result to avoid repeated API calls.

        Returns:
            Sorted list of available module names

        Raises:
            ValueError: If GitHub API request fails
        """
        cache_file = self.cache_dir / "modules_list.txt"

        # Return cached list if available
        if cache_file.exists():
            with open(cache_file, 'r') as f:
                modules = [line.strip() for line in f if line.strip()]
            return modules

        # Fetch modules from GitHub and cache
        modules = self._fetch_modules_iterative()

        # Write to cache file
        with open(cache_file, 'w') as f:
            for module in modules:
                f.write(f"{module}\n")

        return modules


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
