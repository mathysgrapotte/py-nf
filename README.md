# py-nf

Run Nextflow modules directly from Python while keeping access to the full set of runtime signals that Nextflow exposes. This repository wraps the Nextflow JVM classes with [JPype](https://jpype.readthedocs.io) and layers a small Python API on top that:

```python
from pynf import run_module; run_module("nextflow_scripts/file-output-process.nf")
```

Behind that one-liner the library:

* Loads `.nf` scripts and modules without rewriting them.
* Executes them inside a real `nextflow.Session`.
* Collects `WorkflowOutputEvent` / `FilePublishEvent` records so Python receives the same outputs that the CLI would publish.


## Prerequisites

* Python 3.12+ (managed via [uv](https://docs.astral.sh/uv/) in this repo).
* A locally built Nextflow distribution; this project expects the jar at `nextflow/modules/nextflow/build/libs/nextflow-25.08.0-edge-one.jar` (the Gradle build in the nested `nextflow/` directory produces it).
* Nextflow scripts placed under `nextflow_scripts/`. The repo ships a few simple examples:
	* `nextflow_scripts/hello-world.nf` – DSL2 script with a workflow block.
	* `nextflow_scripts/simple-process.nf` – raw module (single `process`) without a `workflow {}` block.
	* `nextflow_scripts/file-output-process.nf` – raw module that publishes `output.txt` and is used in the tests below.


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
8. `session.await_()` (Nextflow’s async await) blocks until all tasks finish.
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
* **Flattening rules** – `_flatten_paths` walks nested Python & Java containers and yields string paths. Strings are treated as leaf nodes so we don’t iterate character-by-character, and Java collections/iterables are handled via their respective iterators.
* **Fallback** – If neither event produced paths (e.g. a custom plugin suppressed them), we fall back to scanning the work directory and return every non-hidden file under each task’s execution folder. This mirrors the earlier prototype behaviour and guarantees backwards compatibility, even if it is noisier.


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

Happy hacking! 🚀

