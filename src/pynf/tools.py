"""
Backend tools for nf-core module management.

Provides convenient wrappers around NFCoreModuleManager for common tasks.
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any
import yaml

from .nfcore import NFCoreModuleManager, NFCoreModule


def list_modules(cache_dir: Optional[Path] = None, github_token: Optional[str] = None) -> list[str]:
    """
    List all available nf-core modules.

    Args:
        cache_dir: Directory to cache modules
        github_token: Optional GitHub token for rate limiting

    Returns:
        Sorted list of module names
    """
    manager = NFCoreModuleManager(cache_dir=cache_dir, github_token=github_token)
    return manager.list_available_modules()


def list_submodules(
    module: str,
    cache_dir: Optional[Path] = None,
    github_token: Optional[str] = None,
) -> list[str]:
    """
    List submodules available in a given module.

    Args:
        module: Module name (e.g., 'samtools')
        cache_dir: Directory to cache modules
        github_token: Optional GitHub token for rate limiting

    Returns:
        Sorted list of submodule names
    """
    manager = NFCoreModuleManager(cache_dir=cache_dir, github_token=github_token)
    return manager.list_submodules(module)


def download_module(
    module: str,
    cache_dir: Optional[Path] = None,
    force: bool = False,
    github_token: Optional[str] = None,
) -> NFCoreModule:
    """
    Download an nf-core module.

    Args:
        module: Module name (e.g., 'fastqc' or 'samtools/view')
        cache_dir: Directory to cache modules
        force: Force re-download even if cached
        github_token: Optional GitHub token for rate limiting

    Returns:
        NFCoreModule object with paths to downloaded files

    Raises:
        ValueError: If module doesn't exist or download fails
    """
    manager = NFCoreModuleManager(cache_dir=cache_dir, github_token=github_token)
    return manager.download_module(module, force=force)


def inspect_module(
    module: str,
    cache_dir: Optional[Path] = None,
    github_token: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Inspect a downloaded module and return its metadata.

    If module is not cached locally, it will be downloaded.

    Args:
        module: Module name
        cache_dir: Directory to cache modules
        github_token: Optional GitHub token for rate limiting

    Returns:
        Dictionary with keys:
        - 'name': Module name
        - 'path': Path to module directory
        - 'meta': Parsed meta.yml as dictionary
        - 'main_nf_lines': Number of lines in main.nf
        - 'main_nf_preview': First 20 lines of main.nf

    Raises:
        ValueError: If module cannot be downloaded or inspected
    """
    manager = NFCoreModuleManager(cache_dir=cache_dir, github_token=github_token)

    # Ensure module is cached
    nf_module = manager.download_module(module)

    # Read and parse meta.yml
    try:
        meta_content = nf_module.meta_yml.read_text()
        meta_dict = yaml.safe_load(meta_content)
    except Exception as e:
        raise ValueError(f"Failed to parse meta.yml: {e}")

    # Read main.nf
    try:
        main_content = nf_module.main_nf.read_text()
        main_lines = main_content.split("\n")
        main_preview = main_lines[:20]
        main_line_count = len(main_lines)
    except Exception as e:
        raise ValueError(f"Failed to read main.nf: {e}")

    return {
        "name": module,
        "path": str(nf_module.local_path),
        "meta": meta_dict,
        "meta_raw": meta_content,
        "main_nf_lines": main_line_count,
        "main_nf_preview": main_preview,
    }


def get_module_inputs(
    module: str,
    cache_dir: Optional[Path] = None,
    github_token: Optional[str] = None,
) -> list[Dict[str, Any]]:
    """
    Extract input parameters from a module's main.nf using Nextflow native API.

    If module is not cached locally, it will be downloaded.

    Args:
        module: Module name
        cache_dir: Directory to cache modules
        github_token: Optional GitHub token for rate limiting

    Returns:
        List of input channel definitions:
        [{'type': str, 'params': [{'type': str, 'name': str}]}]

    Raises:
        ValueError: If module cannot be downloaded or inputs cannot be extracted
    """
    import jpype
    from .engine import NextflowEngine

    manager = NFCoreModuleManager(cache_dir=cache_dir, github_token=github_token)

    # Ensure module is cached
    nf_module = manager.download_module(module)

    # Create engine and extract inputs using native API
    try:
        engine = NextflowEngine()

        # Set up Nextflow session
        Session = jpype.JClass("nextflow.Session")
        ScriptFile = jpype.JClass("nextflow.script.ScriptFile")
        ArrayList = jpype.JClass("java.util.ArrayList")

        session = Session()
        script_file = ScriptFile(jpype.java.nio.file.Paths.get(str(nf_module.main_nf)))
        session.init(script_file, ArrayList(), None, None)
        session.start()

        # Load and parse script
        loader = engine.ScriptLoaderFactory.create(session)
        java_path = jpype.java.nio.file.Paths.get(str(nf_module.main_nf))
        loader.parse(java_path)
        script = loader.getScript()

        # Extract inputs using native API
        inputs = engine._get_process_inputs(loader, script)

        # Cleanup
        session.destroy()

        return inputs

    except Exception as e:
        raise ValueError(f"Failed to extract inputs from main.nf: {e}")


def module_exists_locally(
    module: str,
    cache_dir: Optional[Path] = None,
) -> bool:
    """
    Check if a module exists in the local cache.

    Args:
        module: Module name
        cache_dir: Directory to cache modules (defaults to ./nf-core-modules)

    Returns:
        True if module is cached locally, False otherwise
    """
    if cache_dir is None:
        cache_dir = Path("./nf-core-modules")

    module_dir = cache_dir / module
    main_nf = module_dir / "main.nf"
    meta_yml = module_dir / "meta.yml"

    return main_nf.exists() and meta_yml.exists()


def get_rate_limit_status(
    github_token: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get current GitHub API rate limit status.

    Args:
        github_token: Optional GitHub token

    Returns:
        Dictionary with 'limit', 'remaining', and 'reset_time' (Unix timestamp)

    Raises:
        ValueError: If GitHub API request fails
    """
    manager = NFCoreModuleManager(github_token=github_token)
    return manager.get_rate_limit_status()


def run_nfcore_module(
    module: str,
    inputs: Optional[list] = None,
    params: Optional[Dict[str, Any]] = None,
    executor: str = "local",
    docker_enabled: bool = False,
    cache_dir: Optional[Path] = None,
    github_token: Optional[str] = None,
):
    """
    Run an nf-core module with automatic download if needed.

    Args:
        module: Module name (e.g., 'fastqc')
        inputs: List of dicts, each dict contains parameter names and values for one input channel
               Example: [{'meta': {...}, 'reads': ['file1.fastq', 'file2.fastq']}]
        params: Dictionary of parameters
        executor: Nextflow executor type (default: 'local')
        docker_enabled: Enable Docker execution
        cache_dir: Directory to cache modules
        github_token: Optional GitHub token

    Returns:
        NextflowResult object from execution

    Raises:
        ValueError: If module cannot be found/downloaded
    """
    from pynf import run_module

    # Download module if not cached
    nf_module = download_module(
        module,
        cache_dir=cache_dir,
        github_token=github_token,
    )

    # Configure Docker if enabled
    docker_config = None
    if docker_enabled:
        docker_config = {
            "enabled": True,
            "registry": "quay.io",
        }

    # Execute the module
    return run_module(
        str(nf_module.main_nf),
        inputs=inputs,
        params=params,
        executor=executor,
        docker_config=docker_config,
    )
