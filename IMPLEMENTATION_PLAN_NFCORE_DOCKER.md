# Implementation Plan: Running nf-core Modules with Docker Containers

## Overview

This document outlines the detailed implementation plan for enabling py-nf to run nf-core modules in Docker containers. The plan covers two main aspects:
1. How Nextflow executes containers at the Java level
2. How to fetch and run nf-core modules with proper parameter handling (meta maps)

## Research Findings

### 1. Nextflow Container Architecture

#### Key Java Classes

**Container Builder Hierarchy:**
- `nextflow.container.ContainerBuilder` - Abstract base class for all container runtimes
- `nextflow.container.DockerBuilder` - Docker-specific implementation
- `nextflow.container.DockerConfig` - Docker configuration class (annotated with `@ScopeName("docker")`)

**Location in Nextflow source:**
```
nextflow/modules/nextflow/src/main/groovy/nextflow/container/DockerBuilder.groovy
nextflow/modules/nextflow/src/main/groovy/nextflow/container/DockerConfig.groovy
```

**How it works:**
1. When a Nextflow script specifies a `container` directive, the executor wraps the task execution command
2. The `ContainerBuilder` generates the actual docker run command
3. Container configuration is read from the Nextflow config (e.g., `docker { enabled = true }`)

#### Key Configuration Options

Docker-specific options available in `DockerConfig`:
- `enabled` - Enable Docker execution (boolean)
- `engineOptions` - Additional Docker CLI options
- `runOptions` - Additional options for `docker run`
- `remove` - Auto-remove container after execution (default: true)
- `temp` - Temporary directory in container
- `registry` - Container registry URL override
- `envWhitelist` - Environment variables to pass through

### 2. nf-core Module Structure

#### Module Organization

nf-core modules are stored in GitHub: `https://github.com/nf-core/modules`

Structure:
```
modules/nf-core/{tool-name}/
  ├── main.nf          # Process definition
  ├── meta.yml         # Metadata and documentation
  └── tests/           # Test configurations
```

#### Example: FASTQC Module

**Container specification in main.nf:**
```groovy
process FASTQC {
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/fastqc:0.12.1--hdfd78af_0' :
        'biocontainers/fastqc:0.12.1--hdfd78af_0' }"

    input:
    tuple val(meta), path(reads)

    output:
    tuple val(meta), path("*.html"), emit: html
    tuple val(meta), path("*.zip") , emit: zip
    path "versions.yml"            , emit: versions

    script:
    def prefix = task.ext.prefix ?: "${meta.id}"
    // ... script content
}
```

**Key observations:**
1. Container image is specified at the process level
2. Meta map (`meta`) carries sample metadata through the pipeline
3. Meta map typically contains: `id`, `single_end`, and other sample-specific fields

#### Meta Map Structure

Meta maps are Groovy maps (similar to Python dicts) that contain:
- `id` - Unique sample identifier (required)
- `single_end` - Boolean indicating single-end vs paired-end sequencing
- Other tool-specific fields

Example:
```groovy
meta = [id: 'sample1', single_end: false]
```

## Implementation Plan

### Phase 1: Enable Docker Container Execution

#### File: `src/pynf/engine.py`

**Current state:**
The `execute()` method accepts `executor` parameter but has no container configuration.

**Changes needed:**

1. Add `docker_config` parameter to `execute()` method:

```python
def execute(self, script_path, executor="local", params=None, input_files=None, config=None, docker_config=None):
    """
    Execute a Nextflow script with optional Docker configuration.

    Args:
        docker_config (dict): Docker configuration options:
            - enabled (bool): Enable Docker execution
            - image (str): Docker image to use (optional, can be specified in .nf file)
            - remove (bool): Auto-remove container after execution (default: True)
            - runOptions (str): Additional docker run options
            - temp (str): Temporary directory in container
    """
```

2. Apply Docker configuration to the Session:

```python
def execute(self, script_path, executor="local", params=None, input_files=None, config=None, docker_config=None):
    session = self.Session()

    # Apply Docker configuration if provided
    if docker_config:
        self._configure_docker(session, docker_config)

    # ... rest of execution
```

3. Implement `_configure_docker()` helper method:

```python
def _configure_docker(self, session, docker_config):
    """
    Configure Docker settings for the Nextflow session.

    This method sets up Docker configuration before the session is initialized,
    allowing container execution.
    """
    # Import Java HashMap for configuration
    HashMap = jpype.JClass("java.util.HashMap")

    # Create Docker config map
    config_map = HashMap()

    # Set Docker as enabled
    config_map.put("docker.enabled", docker_config.get("enabled", True))

    # Optional: set docker run options
    if "runOptions" in docker_config:
        config_map.put("docker.runOptions", docker_config["runOptions"])

    # Optional: set auto-remove
    if "remove" in docker_config:
        config_map.put("docker.remove", docker_config["remove"])

    # Apply configuration to session
    # Note: This needs to happen before session.init()
    # We may need to use session.getConfig() and merge settings
    session_config = session.getConfig()
    session_config.putAll(config_map)
```

**Alternative approach (if direct config doesn't work):**

Create a temporary `nextflow.config` file and load it:

```python
def _configure_docker(self, session, docker_config):
    """
    Configure Docker by creating a temporary nextflow.config file.
    """
    import tempfile

    # Create config content
    config_content = """
    docker {
        enabled = true
        remove = ${remove}
        runOptions = '${run_options}'
    }
    """.format(
        remove="true" if docker_config.get("remove", True) else "false",
        run_options=docker_config.get("runOptions", "")
    )

    # Write to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.config', delete=False) as f:
        f.write(config_content)
        config_path = f.name

    # Load config into session
    ConfigBuilder = jpype.JClass("nextflow.config.ConfigBuilder")
    config_file = jpype.java.nio.file.Paths.get(config_path)
    # Apply config to session before init
    # This requires investigation of ConfigBuilder API
```

**Important notes:**
- Docker configuration must be applied BEFORE `session.init()` is called
- We need to investigate the exact Java API for applying config programmatically
- May need to look at how Nextflow CLI applies `-with-docker` flag

### Phase 2: Download nf-core Modules

#### New File: `src/pynf/nfcore.py`

This module will handle fetching nf-core modules from GitHub.

```python
"""
nf-core module management for py-nf.

This module provides utilities to download and use nf-core modules
from the official nf-core/modules repository.
"""

import requests
from pathlib import Path
from typing import Optional, Dict


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
```

**Dependencies to add:**
```bash
uv add requests
```

### Phase 3: Meta Map Parameter Handling

#### Enhancement to `engine.py`

The current `execute()` method accepts `params` as a dict, but we need special handling for meta maps that are used with nf-core modules.

**Concept:**
- nf-core modules expect input as: `tuple val(meta), path(reads)`
- In Python, we need to create this tuple structure and pass it through channels
- The `meta` part is a Map (dict), and `reads` is a Path or list of Paths

**Implementation approach:**

```python
def execute(self, script_path, executor="local", params=None, input_files=None,
            config=None, docker_config=None, meta=None):
    """
    Execute a Nextflow script.

    Args:
        meta (dict): Metadata map for nf-core modules.
                    Example: {'id': 'sample1', 'single_end': False}
                    Will be combined with input_files to create tuple val(meta), path(files)
    """
    session = self.Session()

    # Apply Docker config if provided
    if docker_config:
        self._configure_docker(session, docker_config)

    # Initialize session
    ArrayList = jpype.JClass("java.util.ArrayList")
    ScriptFile = jpype.JClass("nextflow.script.ScriptFile")
    script_file = ScriptFile(jpype.java.nio.file.Paths.get(str(script_path)))
    session.init(script_file, ArrayList(), None, None)
    session.start()

    # Set regular parameters
    if params:
        for key, value in params.items():
            session.getBinding().setVariable(key, value)

    # Handle meta map + input files for nf-core modules
    if meta and input_files:
        input_channel = self._create_meta_channel(session, meta, input_files)
        session.getBinding().setVariable("input", input_channel)
    elif input_files:
        # Legacy behavior: just files without meta
        input_channel = self.Channel.of(*input_files)
        session.getBinding().setVariable("input", input_channel)

    # ... continue with execution
```

**Implement `_create_meta_channel()` method:**

```python
def _create_meta_channel(self, session, meta, input_files):
    """
    Create a Nextflow channel with tuple val(meta), path(files).

    This is the standard input format for nf-core modules.

    Args:
        session: Nextflow session
        meta: Python dict with metadata (e.g., {'id': 'sample1'})
        input_files: List of file paths or single file path

    Returns:
        Nextflow channel containing tuple(meta_map, file_paths)
    """
    # Import Java classes
    HashMap = jpype.JClass("java.util.HashMap")
    ArrayList = jpype.JClass("java.util.ArrayList")

    # Convert Python dict to Java HashMap
    meta_map = HashMap()
    for key, value in meta.items():
        meta_map.put(key, value)

    # Ensure input_files is a list
    if not isinstance(input_files, list):
        input_files = [input_files]

    # Convert file paths to Java Path objects
    file_paths = ArrayList()
    for file_path in input_files:
        java_path = jpype.java.nio.file.Paths.get(str(file_path))
        file_paths.add(java_path)

    # Create a tuple: [meta_map, file_paths]
    # For single file, just use the path directly
    if len(file_paths) == 1:
        tuple_value = ArrayList()
        tuple_value.add(meta_map)
        tuple_value.add(file_paths.get(0))
    else:
        tuple_value = ArrayList()
        tuple_value.add(meta_map)
        tuple_value.add(file_paths)

    # Create channel with this tuple
    channel = self.Channel.of(tuple_value)

    return channel
```

**Add validation for required meta fields:**

```python
def validate_meta_map(meta: dict, required_fields: list[str] = None):
    """
    Validate meta map contains required fields.

    Args:
        meta: Meta map dictionary
        required_fields: List of required field names

    Raises:
        ValueError: If required fields are missing

    Example:
        >>> validate_meta_map({'id': 'sample1'}, required_fields=['id'])
        >>> validate_meta_map({'name': 'test'}, required_fields=['id'])
        ValueError: Missing required meta field: id
    """
    if required_fields is None:
        required_fields = ['id']  # 'id' is always required

    missing_fields = [field for field in required_fields if field not in meta]

    if missing_fields:
        raise ValueError(
            f"Missing required meta fields: {', '.join(missing_fields)}. "
            f"Meta map provided: {meta}"
        )
```

### Phase 4: Integration and Testing

#### New File: `test_nfcore_docker.py`

A standalone test script to validate the implementation:

```python
"""
Test script for running nf-core modules with Docker containers.

This script demonstrates:
1. Downloading an nf-core module (FASTQC)
2. Running it with Docker enabled
3. Providing proper meta map parameters
4. Collecting outputs
"""

from pathlib import Path
from pynf import NextflowEngine
from pynf.nfcore import download_nfcore_module
import tempfile
import shutil


def create_test_fastq():
    """Create a minimal test FASTQ file."""
    test_dir = Path(tempfile.mkdtemp(prefix="pynf_test_"))
    fastq_file = test_dir / "test_sample.fastq.gz"

    # Create a minimal FASTQ content (just a few reads)
    content = """@SEQ_ID_1
GATTTGGGGTTCAAAGCAGTATCGATCAAATAGTAAATCCATTTGTTCAACTCACAGTTT
+
!''*((((***+))%%%++)(%%%%).1***-+*''))**55CCF>>>>>>CCCCCCC65
@SEQ_ID_2
GATTTGGGGTTCAAAGCAGTATCGATCAAATAGTAAATCCATTTGTTCAACTCACAGTTT
+
!''*((((***+))%%%++)(%%%%).1***-+*''))**55CCF>>>>>>CCCCCCC65
"""

    # Write to file (in real scenario, would gzip it)
    with open(fastq_file, 'w') as f:
        f.write(content)

    return test_dir, fastq_file


def test_fastqc_with_docker():
    """
    Test running FASTQC nf-core module with Docker.
    """
    print("=" * 70)
    print("TEST: Running nf-core FASTQC module with Docker")
    print("=" * 70)

    # Step 1: Download the nf-core FASTQC module
    print("\n[1/5] Downloading FASTQC module from nf-core...")
    module = download_nfcore_module('fastqc')
    print(f"    Module downloaded to: {module.local_path}")
    print(f"    Main script: {module.main_nf}")

    # Step 2: Create test input data
    print("\n[2/5] Creating test FASTQ file...")
    test_dir, fastq_file = create_test_fastq()
    print(f"    Test file: {fastq_file}")

    # Step 3: Prepare meta map
    print("\n[3/5] Preparing meta map...")
    meta = {
        'id': 'test_sample_001',
        'single_end': True
    }
    print(f"    Meta map: {meta}")

    # Step 4: Configure Docker
    print("\n[4/5] Configuring Docker...")
    docker_config = {
        'enabled': True,
        'remove': True,  # Auto-remove container after execution
        'runOptions': '--memory=2g --cpus=2'  # Optional resource limits
    }
    print(f"    Docker config: {docker_config}")

    # Step 5: Execute the module
    print("\n[5/5] Executing FASTQC module...")
    engine = NextflowEngine()

    try:
        result = engine.execute(
            script_path=module.main_nf,
            executor='local',
            input_files=[str(fastq_file)],
            meta=meta,
            docker_config=docker_config
        )

        print("\n" + "=" * 70)
        print("RESULTS")
        print("=" * 70)

        # Display outputs
        print("\nOutput files generated:")
        output_files = result.get_output_files()
        for file_path in output_files:
            print(f"  - {file_path}")

        # Check for expected outputs
        html_files = [f for f in output_files if f.endswith('.html')]
        zip_files = [f for f in output_files if f.endswith('.zip')]

        print(f"\nHTML reports: {len(html_files)}")
        print(f"ZIP archives: {len(zip_files)}")

        # Display workflow outputs
        print("\nWorkflow outputs:")
        workflow_outputs = result.get_workflow_outputs()
        for output in workflow_outputs:
            print(f"  {output['name']}: {output['value']}")

        # Display execution report
        print("\nExecution report:")
        report = result.get_execution_report()
        print(f"  Completed tasks: {report['completed_tasks']}")
        print(f"  Failed tasks: {report['failed_tasks']}")
        print(f"  Work directory: {report['work_dir']}")

        print("\n" + "=" * 70)
        print("TEST PASSED ✓")
        print("=" * 70)

        return True

    except Exception as e:
        print("\n" + "=" * 70)
        print("TEST FAILED ✗")
        print("=" * 70)
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Cleanup test files
        print("\nCleaning up test files...")
        shutil.rmtree(test_dir)


def test_samtools_view_with_docker():
    """
    Test running SAMTOOLS/VIEW module with Docker.

    This demonstrates a more complex module with multiple inputs.
    """
    print("\n\n")
    print("=" * 70)
    print("TEST: Running nf-core SAMTOOLS/VIEW module with Docker")
    print("=" * 70)

    # Download module
    print("\n[1/4] Downloading SAMTOOLS/VIEW module...")
    module = download_nfcore_module('samtools/view')

    # This would require a BAM file as input
    print("[2/4] This test requires a BAM file (skipping for now)")
    print("    To run this test, provide a test BAM file")

    print("\nModule downloaded successfully ✓")
    print(f"    Location: {module.local_path}")

    return True


if __name__ == '__main__':
    # Run tests
    print("Starting nf-core Docker integration tests...\n")

    test1_passed = test_fastqc_with_docker()
    test2_passed = test_samtools_view_with_docker()

    print("\n\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"FASTQC test: {'PASSED ✓' if test1_passed else 'FAILED ✗'}")
    print(f"SAMTOOLS/VIEW test: {'PASSED ✓' if test2_passed else 'FAILED ✗'}")
    print("=" * 70)
```

### Phase 5: Update Project Files

#### Update `src/pynf/__init__.py`

Add exports for new functionality:

```python
from .engine import NextflowEngine
from .result import NextflowResult
from .nfcore import (
    download_nfcore_module,
    NFCoreModule,
    NFCoreModuleManager
)

def run_module(path, input_files=None, params=None, executor="local",
               docker_config=None, meta=None):
    """
    Convenience function to run a Nextflow module.

    Args:
        docker_config: Docker configuration dict
        meta: Meta map for nf-core modules
    """
    engine = NextflowEngine()
    script_path = engine.load_script(path)
    return engine.execute(
        script_path,
        executor=executor,
        params=params,
        input_files=input_files,
        docker_config=docker_config,
        meta=meta
    )

__all__ = [
    'NextflowEngine',
    'NextflowResult',
    'run_module',
    'download_nfcore_module',
    'NFCoreModule',
    'NFCoreModuleManager',
]
```

#### Update `.gitignore`

Add downloaded modules directory:

```
# nf-core modules cache
nf-core-modules/
```

#### Update `pyproject.toml`

Add new dependency:

```toml
[project]
dependencies = [
    "jpype1>=1.4.1",
    "python-dotenv>=1.0.0",
    "requests>=2.31.0",  # Add this
]
```

## Implementation Steps

### Step 1: Docker Configuration (Critical Path)

This is the most complex part because we need to figure out the exact Java API for configuring Docker in a Nextflow Session.

**Investigation needed:**
1. Look at Nextflow source code for how CLI applies `-with-docker` flag
2. Understand `ConfigBuilder` and how to programmatically set config
3. Test different approaches:
   - Direct session config manipulation
   - Temporary config file
   - Environment variables

**Files to examine in Nextflow source:**
- `nextflow/modules/nextflow/src/main/groovy/nextflow/cli/CmdRun.groovy` - CLI implementation
- `nextflow/modules/nextflow/src/main/groovy/nextflow/config/ConfigBuilder.groovy` - Config building

### Step 2: Module Download (Easy)

Straightforward HTTP requests to GitHub raw URLs.

**Testing:**
```python
# Test manually first
from pynf.nfcore import download_nfcore_module
module = download_nfcore_module('fastqc')
print(module.main_nf.read_text())
```

### Step 3: Meta Map Handling (Medium)

Converting Python dicts to Java HashMaps is straightforward with JPype, but we need to ensure the tuple structure matches what Nextflow expects.

**Testing strategy:**
1. First test with simple `Channel.of()` and meta map
2. Check what Java objects Nextflow receives
3. Verify meta map is accessible in the process via `meta.id`, etc.

### Step 4: Integration Testing

Run the full test script and debug issues:

```bash
uv run python test_nfcore_docker.py
```

## Potential Challenges

### 1. Docker Configuration API

**Challenge:** Finding the right Java API to enable Docker programmatically.

**Solutions:**
- Option A: Use `ConfigBuilder` to build config and apply before session init
- Option B: Create temporary `nextflow.config` file
- Option C: Set system properties or environment variables that Nextflow reads
- Option D: Directly manipulate session config after init but before execution

### 2. Container Image Specification

**Challenge:** nf-core modules specify containers using conditional logic based on `workflow.containerEngine`.

**Solution:**
- When running with Docker, the module will automatically select the Docker image
- We just need to ensure `workflow.containerEngine == 'docker'` is set
- This should happen automatically when `docker.enabled = true`

### 3. Meta Map Tuple Structure

**Challenge:** Ensuring the tuple structure `[meta, [file1, file2]]` matches Nextflow expectations.

**Solution:**
- Use JPype's ArrayList to create the tuple
- For single files: `[meta, file]`
- For multiple files: `[meta, [file1, file2]]`
- Test with debug logging to see what Nextflow receives

### 4. Module Dependencies

**Challenge:** Some nf-core modules depend on other modules (subworkflows).

**Solution:**
- For initial implementation, focus on standalone modules (like FASTQC)
- Later, enhance to download module dependencies
- Use `meta.yml` to identify dependencies

## Testing Strategy

### Unit Tests

1. Test Docker config creation (mock Session)
2. Test module download with mocked HTTP requests
3. Test meta map conversion (Python dict → Java HashMap)

### Integration Tests

1. Test FASTQC with minimal FASTQ file
2. Test without Docker (local execution)
3. Test with Docker enabled
4. Test error handling (missing meta.id, invalid module name, etc.)

### Manual Testing

1. Run against real nf-core modules
2. Verify Docker containers are pulled and executed
3. Check outputs are collected correctly
4. Verify containers are cleaned up after execution

## Example Usage (After Implementation)

```python
from pynf import NextflowEngine
from pynf.nfcore import download_nfcore_module

# Download nf-core FASTQC module
module = download_nfcore_module('fastqc')

# Prepare inputs
meta = {'id': 'my_sample', 'single_end': True}
input_files = ['data/sample1.fastq.gz']

# Configure Docker
docker_config = {
    'enabled': True,
    'remove': True,
    'runOptions': '--memory=4g'
}

# Run the module
engine = NextflowEngine()
result = engine.execute(
    script_path=module.main_nf,
    meta=meta,
    input_files=input_files,
    docker_config=docker_config
)

# Get results
outputs = result.get_output_files()
print(f"FASTQC generated {len(outputs)} output files")
for output in outputs:
    print(f"  - {output}")
```

## Next Steps

1. **Create new branch**: `git checkout -b feature/nfcore-docker-support`
2. **Implement in order**:
   - Phase 1: Docker configuration
   - Phase 2: Module downloader
   - Phase 3: Meta map handling
   - Phase 4: Integration testing
3. **Test thoroughly** with real nf-core modules
4. **Document** in README with examples
5. **Commit frequently** as per project guidelines

## References

- nf-core modules repository: https://github.com/nf-core/modules
- Nextflow container documentation: https://www.nextflow.io/docs/latest/container.html
- Nextflow Docker config: https://www.nextflow.io/docs/latest/config.html#scope-docker
- JPype documentation: https://jpype.readthedocs.io/
