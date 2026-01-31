# pynextflow

Run Nextflow modules directly from Python while keeping access to the full set of runtime signals that Nextflow exposes. This repository wraps the Nextflow JVM classes with [JPype](https://jpype.readthedocs.io) and layers a small Python API on top.

**Two ways to use pynextflow:**

1. **Python API** - Direct programmatic control over Nextflow execution
2. **CLI Tools** - Command-line interface for managing and running nf-core modules

```python
from pynf import run_script; run_script("nextflow_scripts/file-output-process.nf")
```

Behind that one-liner the library:

* Loads `.nf` scripts and modules without rewriting them.
* Executes them inside a real `nextflow.Session`.
* Collects `WorkflowOutputEvent` / `FilePublishEvent` records so Python receives the same outputs that the CLI would publish.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Nextflow Setup](#nextflow-setup)
- [Installation & test drive](#installation--test-drive)
- [Quick start](#quick-start)
- [CLI Tools](#cli-tools)
- [API tour](#api-tour)
- [Output collection details](#output-collection-details)
- [Working with raw modules](#working-with-raw-modules-nf-without-workflow-)
- [Caveats & tips](#caveats--tips)
- [Extending the library](#extending-the-library)
- [Further reading](#further-reading)
- [Manual Setup](#manual-setup)

## Prerequisites

* Python 3.12+ (managed via [uv](https://docs.astral.sh/uv/) in this repo).
* Java 17+ (required to build Nextflow)
* Git and Make (for cloning and building Nextflow)
* Nextflow scripts placed under `nextflow_scripts/`. The repo ships a few simple examples:
	* `nextflow_scripts/hello-world.nf` – DSL2 script with a workflow block.
	* `nextflow_scripts/simple-process.nf` – raw module (single `process`) without a `workflow {}` block.
	* `nextflow_scripts/file-output-process.nf` – raw module that publishes `output.txt` and is used in the tests below.

## Nextflow Setup

This project requires a locally built Nextflow fat JAR. An automated setup script handles this for you:

```bash
python setup_nextflow.py
```

This will:
1. Create a `.env` file with the Nextflow JAR path
2. Clone the Nextflow repository
3. Build the Nextflow fat JAR (includes all dependencies)
4. Verify the setup

**Options:**
- `--force` – Rebuild even if JAR already exists
- `--version v25.10.0` – Build a specific Nextflow version

**Manual setup (alternative):**
If you prefer to set up manually, see the [Manual Setup](#manual-setup) section at the end of this document.

## Installation & test drive

Create the virtual environment and install dependencies:

```bash
uv sync
```

Run the integration test that exercises `file-output-process.nf`:

```bash
uv run pytest tests/test_integration.py::test_file_output_process_outputs_output_txt
```

You should see `output.txt` captured in Python without tunnelling through the work directory.

### Module test data (samtools/view)

The samtools/view validation and verbose scripts expect local input files in the
repo root. The files are gitignored so you can download them on demand:

```bash
curl -fL -o test.bam "https://raw.githubusercontent.com/nf-core/test-datasets/modules/data/genomics/sarscov2/illumina/bam/test.paired_end.sorted.bam"
curl -fL -o test.bam.bai "https://raw.githubusercontent.com/nf-core/test-datasets/modules/data/genomics/sarscov2/illumina/bam/test.paired_end.sorted.bam.bai"
curl -fL -o reference.fa "https://raw.githubusercontent.com/nf-core/test-datasets/modules/data/genomics/homo_sapiens/genome/genome.fasta"
printf "read1\n" > readnames.txt
```

These inputs are used by:

- `tests/test_multi_input_validation.py`
- `tests/test_verbose_mode.py`

## Quick start

```python
from pathlib import Path

from pynf import run_module
from pynf.execution import execute_nextflow
from pynf.types import ExecutionRequest

# Option 1 — functional API
request = ExecutionRequest(script_path=Path("nextflow_scripts/file-output-process.nf"))
result = execute_nextflow(request)

print("Files published:", result.get_output_files())
print("Structured workflow outputs:", result.get_workflow_outputs())

# Option 2 — convenience helper
result = run_script("nextflow_scripts/file-output-process.nf")
assert any(Path(p).name == "output.txt" for p in result.get_output_files())
```

### Running an nf-core module from Python

```python
from pathlib import Path

from pynf import ExecutionRequest, run_nfcore_module

request = ExecutionRequest(
    # Note: script_path is ignored for nf-core runs; the cached module's main.nf is used.
    script_path=Path("."),
    inputs=[{"meta": {"id": "sample1"}, "reads": ["sample.fastq"]}],
)
result = run_nfcore_module("fastqc", request)
print(result.get_output_files())
```

## CLI Tools

The `pynf` command-line interface provides easy access to nf-core modules without writing Python code.

### Installation

After running `uv sync`, the `pynf` command is available:

```bash
pynf --help
```

### Global Options

- `--cache-dir <path>` - Directory to cache modules (default: `./nf-core-modules`)
- `--github-token <token>` - GitHub personal access token for higher API rate limits (can also use `GITHUB_TOKEN` env var)

### Module identifiers

`pynf` uses module identifiers relative to the `nf-core/modules` repository under `modules/nf-core/`.

- Top-level modules: `fastqc`, `bcftools`, `samtools`
- Submodules: `samtools/view`, `samtools/sort`

For convenience, callers may also pass `nf-core/<id>`; the prefix is ignored.

### Commands

#### `list-modules-cmd` - List available nf-core modules

```bash
pynf list-modules-cmd

# Limit output
pynf list-modules-cmd --limit 50

# Show GitHub API rate limit status
pynf list-modules-cmd --rate-limit
```

#### `list-submodules` - List submodules for a specific module

```bash
pynf list-submodules samtools
pynf list-submodules bcftools
```

#### `download` - Download an nf-core module

```bash
pynf download fastqc

# Force re-download even if cached
pynf download fastqc --force
```

#### `list-inputs` - Show input parameters from meta.yml

```bash
pynf list-inputs fastqc

# Output as JSON
pynf list-inputs fastqc --json
```

#### `inspect` - Inspect a module's metadata and code

```bash
pynf inspect fastqc

# JSON output
pynf inspect fastqc --json
```

#### `run` - Execute an nf-core module

```bash
# Basic execution
pynf run fastqc --inputs '[{"meta": {"id": "sample1"}, "reads": ["sample.fastq"]}]'

# With parameters
pynf run fastqc \
  --inputs '[{"meta": {"id": "sample1"}, "reads": ["data/sample.fastq"]}]' \
  --params '{"quality_threshold": 20}'

# Enable Docker (recommended for nf-core modules)
pynf run fastqc \
  --inputs '[{"meta": {"id": "sample1"}, "reads": ["sample.fastq"]}]' \
  --docker

# Verbose output for debugging
pynf run fastqc \
  --inputs '[{"meta": {"id": "sample1"}, "reads": ["sample.fastq"]}]' \
  --verbose

# Use different executor
pynf run fastqc \
  --inputs '[{"meta": {"id": "sample1"}, "reads": ["sample.fastq"]}]' \
  --executor slurm
```

**Input format:** The `--inputs` parameter must be a JSON list of dictionaries. Each dictionary represents one input channel group with keys matching the module's input specification.

**Common input patterns:**
- Single-end reads: `[{"meta": {"id": "sample1"}, "reads": ["sample.fastq"]}]`
- Paired-end reads: `[{"meta": {"id": "sample1"}, "reads": ["R1.fastq", "R2.fastq"]}]`
- BAM files: `[{"meta": {"id": "sample1"}, "input": ["sample.bam"], "index": []}]`

## API tour

### `pynf.NextflowResult`

Returned by `pynf.execution.execute_nextflow`. Important accessors:

| Method | Purpose |
| --- | --- |
| `get_output_files()` | Primary way to discover produced files. First flattens the data present in `WorkflowOutputEvent` and `FilePublishEvent` (via `_collect_paths_from_observer`). If none are present, it falls back to scanning the `.nextflow/work` directory (legacy behaviour, still useful for custom operators that bypass the publishing API). |
| `get_workflow_outputs()` | Returns each `WorkflowOutputEvent` as a structured dict: `{name, value, index}` with Java objects converted to plain Python containers. Handy for retrieving channel items emitted by `emit:` statements. |
| `get_process_outputs()` | Introspects `nextflow.script.ScriptMeta` to expose declared process outputs (names and counts) without running another pass over the workdir. |
| `get_stdout()` | Reads `.command.out` from the first task directory, giving you stdout for debugging. |
| `get_execution_report()` | Summarises `completed_tasks`, `failed_tasks`, and the work directory path. |

### Convenience helpers

`pynf.run_script(path, inputs=None, params=None, executor="local")` is a small convenience wrapper for running an arbitrary `.nf` script. It returns a `NextflowResult`.

## Output collection details

* **Primary signal** – `onWorkflowOutput` provides the values emitted by `emit:` blocks and named workflow outputs.
* **Secondary signal** – `onFilePublish` captures files that Nextflow publishes or that a process declares as `output: path`. Both callbacks arrive with Java objects (often nested lists/maps of `java.nio.file.Path`).
* **Flattening rules** – `_flatten_paths` walks nested Python & Java containers and yields string paths. Strings are treated as leaf nodes so we don't iterate character-by-character, and Java collections/iterables are handled via their respective iterators.
* **Fallback** – If neither event produced paths (e.g. a custom plugin suppressed them), we fall back to scanning the work directory and return every non-hidden file under each task's execution folder. This mirrors the earlier prototype behaviour and guarantees backwards compatibility, even if it is noisier.

## Working with raw modules (.nf without `workflow {}`)

* Nextflow automatically wraps a single-process module in a synthetic workflow; our engine does **not** force `ScriptMeta.isModule()` like previous iterations. As long as you call `execute_nextflow(ExecutionRequest(...))` the implicit workflow is triggered.
* The integration test `tests/test_integration.py::test_file_output_process_outputs_output_txt` demonstrates this: the raw module in `nextflow_scripts/file-output-process.nf` produces `output.txt`, and the observer captures it without having to add a manual `workflow { writeFile() }` block.

## Caveats & tips

* **JVM lifecycle** – The first call to `execute_nextflow` starts the JVM. Subsequent instances reuse it; shutting it down requires killing the Python process.
* **JPype warnings** – You may see warnings about restricted native access or `sun.misc.Unsafe`. They are benign for now but you can silence them by launching Python with `JAVA_TOOL_OPTIONS=--enable-native-access=ALL-UNNAMED`.
* **Session reuse** – Each `execute` call spins up a fresh `nextflow.Session`. Reuse the same Python process across runs to avoid re-starting the JVM, but do not reuse a `NextflowResult` once the session is destroyed.
* **Inputs & params** – `input_files` currently sets a single channel named `input`. If your module expects more complex channel wiring you can adapt the helper or push additional channels via `session.getBinding().setVariable` before `loader.runScript()`.
* **Work directory cleanup** – Nextflow will keep its `.nextflow` and `work/` directories unless you remove them. The fallback scanner reads from `session.getWorkDir()`, so deleting the workdir during execution will break the legacy path collection.
* **Nextflow versions** – The observer wiring relies on `TraceObserverV2` (available in Nextflow 23.10+). Running against an earlier jar will fail when we attempt to access `Session.observersV2`.

## Extending the library

The engine intentionally exposes the underlying `session` and `loader` through `NextflowResult`. That means you can reach into the Nextflow APIs when you need advanced behaviour (e.g. retrieving DAG stats or manipulating channels) without waiting for a Python wrapper. Prefer adding thin helpers in `pynf.result` when you find recurring patterns so we maintain Pythonic ergonomics.

## Further reading

* The integration tests under `tests/` show how to assert against workflow outputs.
* `notes/nextflow.md` contains low-level notes on how auto-workflow detection, observers, and fallback scanning behave internally.

## Manual Setup

If you prefer to set up Nextflow manually instead of using the automated script:

1. **Create `.env` file:**
   ```bash
   cp .env.example .env
   ```

2. **Clone Nextflow repository:**
   ```bash
   git clone https://github.com/nextflow-io/nextflow.git
   ```

3. **Build the fat JAR:**
   ```bash
   cd nextflow
   make pack
   ```

4. **Update `.env` with the correct JAR path:**
   ```bash
   # Edit .env to point to: nextflow/build/releases/nextflow-25.10.0-one.jar
   ```

5. **Verify setup:**
   ```bash
   uv run python tests/test_integration.py
   ```

Happy hacking!
