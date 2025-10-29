# py-nf

Run Nextflow modules directly from Python while keeping access to the full set of runtime signals that Nextflow exposes. This repository wraps the Nextflow JVM classes with [JPype](https://jpype.readthedocs.io) and layers a small Python API on top.

**Three ways to use py-nf:**

1. **Python API** - Direct programmatic control over Nextflow execution
2. **CLI Tools** - Command-line interface for managing and running nf-core modules
3. **AI Agent** - Natural language interface powered by LLMs for bioinformatics workflows

```python
from pynf import run_module; run_module("nextflow_scripts/file-output-process.nf")
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
- [Agentic Framework](#agentic-framework)
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


## Quick start

```python
from pathlib import Path

from pynf import NextflowEngine, run_module

# Option 1 — manual control
engine = NextflowEngine()
script_path = engine.load_script("nextflow_scripts/file-output-process.nf")
result = engine.execute(script_path)

print("Files published:", result.get_output_files())
print("Structured workflow outputs:", result.get_workflow_outputs())

# Option 2 — convenience helper
result = run_module("nextflow_scripts/file-output-process.nf")
assert any(Path(p).name == "output.txt" for p in result.get_output_files())
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


## Agentic Framework

The `pynf-agent` provides an AI-powered conversational interface for bioinformatics workflows. Ask questions in natural language and let the agent discover, configure, and execute nf-core modules for you.

### Overview

The agent combines:
- **OpenRouter** - Access to various LLM providers (Claude, GPT-4, etc.)
- **smolagents** - Lightweight agentic framework from HuggingFace
- **LiteLLM** - Unified interface for LLM APIs
- **pynf** - Nextflow execution engine

The agent can autonomously:
- Search for appropriate nf-core modules
- Inspect module requirements and metadata
- Execute workflows with proper inputs
- Track execution history
- Read and analyze output files
- Search the web for bioinformatics information

### Prerequisites

1. **OpenRouter API key** - Sign up at [openrouter.ai](https://openrouter.ai)

```bash
export OPENROUTER_API_KEY='your-key-here'
# Or add to .env file in your project directory
```

2. **Optional dependencies** (for web search)

```bash
uv add duckduckgo-search
```

### Interactive CLI Usage

Start the interactive agent:

```bash
pynf-agent
```

**Options:**
- `--model <model>` - OpenRouter model to use (default: `anthropic/claude-3.5-sonnet`)
- `--workspace <path>` - Working directory for outputs (default: `./agent_workspace`)
- `--verbose` - Enable verbose output

**Example session:**

```bash
$ pynf-agent

┌─────────────────────────────────────────────────────────────────┐
│ # pynf-agent                                                    │
│                                                                 │
│ **Interactive AI Assistant for Bioinformatics Workflows**      │
│                                                                 │
│ Powered by Nextflow + OpenRouter + smollagents                 │
│                                                                 │
│ Type your requests in natural language and the agent will:     │
│ - Search for and download nf-core modules                      │
│ - Execute bioinformatics workflows                             │
│ - Inspect outputs and results                                  │
│ - Search the web for information                               │
│                                                                 │
│ Type 'exit' or 'quit' to end the session.                      │
└─────────────────────────────────────────────────────────────────┘

✓ Agent initialized
  Model: anthropic/claude-3.5-sonnet
  Workspace: /home/user/project/agent_workspace

> Run quality control analysis on my fastq file.

Agent:
I'll help you run quality control analysis on your FASTQ file. Let me search
for the appropriate tool and execute it.

[Agent automatically:]
1. Lists available nf-core modules
2. Identifies fastqc as the appropriate tool
3. Downloads and inspects the fastqc module
4. Asks you for the file path
5. Executes fastqc with proper inputs
6. Reports the results and output files

Output files:
  - /path/to/work/sample_fastqc.html
  - /path/to/work/sample_fastqc.zip

> What's in the HTML report?

[Agent reads and summarizes the HTML file]

> exit
```

### Programmatic Usage

You can also use the agent programmatically in Python scripts:

```python
from pynf_agent import BioinformaticsAgent
from pynf_agent.tools import (
    WebSearchTool,
    ListNFCoreModulesTool,
    ListSubmodulesTool,
    GetModuleInfoTool,
    RunNFModuleTool,
    ListOutputFilesTool,
    ReadFileTool,
    ListDirectoryTool,
)

# Initialize agent
agent = BioinformaticsAgent(
    working_dir="./my_workspace"
)

# Get session context
context = agent.get_context()

# Initialize tools
tools = [
    WebSearchTool(),
    ListNFCoreModulesTool(),
    ListSubmodulesTool(),
    GetModuleInfoTool(),
    RunNFModuleTool(session_context=context),
    ListOutputFilesTool(session_context=context),
    ReadFileTool(),
    ListDirectoryTool(),
]

# Set tools
agent.set_tools(tools)

# Send queries
response = agent.chat("List available nf-core modules")
print(response)

response = agent.chat("What submodules are available for samtools?")
print(response)

# Check execution history
summary = context.get_execution_summary()
print(f"Total executions: {summary['total_executions']}")
print(f"Successful: {summary['successful']}")
```

**See also:** `examples/agent_demo.py` for a complete programmatic usage example.

### Available Agent Tools

The agent has access to 8 specialized tools:

1. **web_search** - Search the web for bioinformatics information, protocols, troubleshooting
2. **list_nfcore_modules** - Discover available nf-core modules
3. **list_submodules** - List submodules within a specific module (e.g., samtools/view, samtools/sort)
4. **get_module_info** - Download and inspect module metadata, inputs, outputs, and requirements
5. **run_nf_module** - Execute a Nextflow module with specified inputs and parameters (Docker enabled by default)
6. **list_output_files** - List output files from previous executions
7. **read_file** - Read and inspect file contents (useful for reports, logs)
8. **list_directory** - Explore directory contents to find input files

### Session Context and Execution Tracking

The agent maintains a session context that tracks:
- All module executions (successful and failed)
- Input parameters used
- Output files generated
- Execution timestamps
- Error messages

This allows the agent to:
- Reference outputs from previous executions
- Chain workflows together
- Provide execution summaries
- Debug failures

### Supported Models

Any OpenRouter-supported model can be used. Recommended models:

- `anthropic/claude-3.5-sonnet` (default) - Best for complex workflows
- `anthropic/claude-3-haiku` - Faster, more economical
- `openai/gpt-4-turbo` - Alternative high-quality option
- `meta-llama/llama-3.1-70b-instruct` - Open source option

Specify with `--model` flag or in the `BioinformaticsAgent` constructor.


## API tour

### `pynf.NextflowEngine`

| Method | Description |
| --- | --- |
| `__init__(nextflow_jar_path=...)` | Starts the JVM (if needed) with the Nextflow jar in the classpath and caches the key Nextflow classes (`Session`, `ScriptLoaderFactory`, etc.). |
| `load_script(path)` | Returns a `pathlib.Path` pointing to the `.nf` file. No parsing occurs yet; this is mostly a convenience to keep a common entry point for module vs. script workflows. |
| `execute(path, executor="local", params=None, input_files=None, config=None)` | Spins up a real `nextflow.Session`, registers an internal observer, parses the script with `ScriptLoaderV2`, and runs it. Returns a `NextflowResult`. Parameters and input channels are pushed into the session binding before execution. |

Execution sequence inside `execute`:

1. Instantiate `nextflow.Session` and call `session.init(...)` with the script file.
2. `session.start()` creates the executor service and registers built-in observers.
3. Optional `params` and `input_files` are loaded into the binding (`session.getBinding().setVariable`).
4. `ScriptLoaderFactory.create(session).parse(path)` builds the AST and decides whether the file is a DSL2 script or a raw module.
5. A custom `TraceObserverV2` proxy (`_WorkflowOutputCollector`) is appended to `session.observersV2` so we capture `WorkflowOutputEvent` and `FilePublishEvent` callbacks.
6. `loader.runScript()` executes the Groovy stub. For raw modules (no `workflow {}`) Nextflow automatically emits a workflow block for the single entry process — no extra handling is required.
7. `session.fireDataflowNetwork(False)` ignites the dataflow network, mirroring what the CLI does.
8. `session.await_()` (Nextflow's async await) blocks until all tasks finish.
9. The observer is removed to avoid leaking proxies between runs.

### `pynf.NextflowResult`

Returned by `NextflowEngine.execute`. Important accessors:

| Method | Purpose |
| --- | --- |
| `get_output_files()` | Primary way to discover produced files. First flattens the data present in `WorkflowOutputEvent` and `FilePublishEvent` (via `_collect_paths_from_observer`). If none are present, it falls back to scanning the `.nextflow/work` directory (legacy behaviour, still useful for custom operators that bypass the publishing API). |
| `get_workflow_outputs()` | Returns each `WorkflowOutputEvent` as a structured dict: `{name, value, index}` with Java objects converted to plain Python containers. Handy for retrieving channel items emitted by `emit:` statements. |
| `get_process_outputs()` | Introspects `nextflow.script.ScriptMeta` to expose declared process outputs (names and counts) without running another pass over the workdir. |
| `get_stdout()` | Reads `.command.out` from the first task directory, giving you stdout for debugging. |
| `get_execution_report()` | Summarises `completed_tasks`, `failed_tasks`, and the work directory path. |

### Convenience helpers

`pynf.run_module(path, input_files=None, params=None, executor="local")` wraps the two-step load/execute call into a single function. It always returns a `NextflowResult` and is designed for the common case where you only need one module run.


## Output collection details

* **Primary signal** – `onWorkflowOutput` provides the values emitted by `emit:` blocks and named workflow outputs.
* **Secondary signal** – `onFilePublish` captures files that Nextflow publishes or that a process declares as `output: path`. Both callbacks arrive with Java objects (often nested lists/maps of `java.nio.file.Path`).
* **Flattening rules** – `_flatten_paths` walks nested Python & Java containers and yields string paths. Strings are treated as leaf nodes so we don't iterate character-by-character, and Java collections/iterables are handled via their respective iterators.
* **Fallback** – If neither event produced paths (e.g. a custom plugin suppressed them), we fall back to scanning the work directory and return every non-hidden file under each task's execution folder. This mirrors the earlier prototype behaviour and guarantees backwards compatibility, even if it is noisier.


## Working with raw modules (.nf without `workflow {}`)

* Nextflow automatically wraps a single-process module in a synthetic workflow; our engine does **not** force `ScriptMeta.isModule()` like previous iterations. As long as you call `engine.execute(...)` the implicit workflow is triggered.
* The integration test `tests/test_integration.py::test_file_output_process_outputs_output_txt` demonstrates this: the raw module in `nextflow_scripts/file-output-process.nf` produces `output.txt`, and the observer captures it without having to add a manual `workflow { writeFile() }` block.


## Caveats & tips

* **JVM lifecycle** – The first `NextflowEngine` instantiation starts the JVM. Subsequent instances reuse it; shutting it down requires killing the Python process.
* **JPype warnings** – You may see warnings about restricted native access or `sun.misc.Unsafe`. They are benign for now but you can silence them by launching Python with `JAVA_TOOL_OPTIONS=--enable-native-access=ALL-UNNAMED`.
* **Session reuse** – Each `execute` call spins up a fresh `nextflow.Session`. Reuse a single `NextflowEngine` across runs to avoid re-starting the JVM, but do not reuse a `NextflowResult` once the session is destroyed.
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

Happy hacking! 🚀
