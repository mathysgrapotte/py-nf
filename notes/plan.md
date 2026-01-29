# Complete Python-JPype Nextflow Integration Plan (historical)

> This document is a historical planning artifact.
>
> Current package layout lives under `src/pynf/` and the preferred entry points are
> the functional API (`pynf.run_module`, `pynf.api.run_script`, `pynf.api.run_module`) plus
> `ExecutionRequest`.

## 1. **Project Setup & Dependencies**
- Update `pyproject.toml`: Add `jpype1` dependency
- Build Nextflow JAR: `cd nextflow && make assemble` to create `nextflow-all.jar`
- Create Python package structure: `py_nf/engine.py`, `py_nf/result.py`, `py_nf/__init__.py`

## 2. **Core Engine Implementation (`py_nf/engine.py`)**
```python
import jpype
import jpype.imports
from pathlib import Path

(Historical note: this plan referenced `NextflowEngine`, which has since been removed in favor of the functional API `ExecutionRequest` + `execute_nextflow`.)

class NextflowEngine:
    def __init__(self, nextflow_jar_path="nextflow/build/libs/nextflow-all.jar"):
        # Start JVM with Nextflow classpath
        jpype.startJVM(classpath=[nextflow_jar_path])

        # Import Nextflow classes
        from nextflow.script import ScriptRunner, ScriptLoader
        from nextflow import Session, Channel
        from nextflow.executor.local import LocalExecutor
        from nextflow.executor import SlurmExecutor

        self.ScriptRunner = ScriptRunner
        self.ScriptLoader = ScriptLoader
        self.Session = Session
        self.Channel = Channel
        self.executors = {"local": LocalExecutor, "slurm": SlurmExecutor}

    def load_script(self, nf_file_path):
        loader = self.ScriptLoader()
        return loader.parse(Path(nf_file_path))

    def execute(self, script, executor="local", params=None, input_files=None, config=None):
        # Create session with config
        session_config = config or {}
        session = self.Session(session_config)

        # Set parameters (params.in = "file.fa")
        if params:
            for key, value in params.items():
                session.getBinding().setVariable(key, value)

        # Create input channels if files provided
        if input_files:
            input_channel = self.Channel.of(*input_files)
            session.getBinding().setVariable("input", input_channel)

        # Execute script
        runner = self.ScriptRunner(session)
        result = runner.setScript(script).execute()

        return NextflowResult(result, session)
```

## 3. **Result Handler (`py_nf/result.py`)**
```python
class NextflowResult:
    def __init__(self, groovy_result, session):
        self.result = groovy_result
        self.session = session

    def get_output_files(self):
        """Extract output file paths from Nextflow execution"""
        outputs = []
        # Navigate through session work directory
        work_dir = self.session.getWorkDir()
        # Collect all output files from completed tasks
        for task_dir in work_dir.listFiles():
            if task_dir.isDirectory():
                outputs.extend([str(f) for f in task_dir.listFiles()])
        return outputs

    def get_stdout(self):
        """Get stdout from processes"""
        return str(self.result.getStdout()) if hasattr(self.result, 'getStdout') else ""

    def get_execution_report(self):
        """Get execution statistics"""
        return {
            'completed_tasks': self.session.getCompletedCount(),
            'failed_tasks': self.session.getFailedCount(),
            'work_dir': str(self.session.getWorkDir())
        }
```

## 4. **Public API (`py_nf/__init__.py`)**
```python
from .engine import NextflowEngine
from .result import NextflowResult

__all__ = ['NextflowEngine', 'NextflowResult']

# Convenience function
def run_workflow(nf_file, input_files=None, params=None, executor="local"):
    """Simple one-liner workflow execution"""
    engine = NextflowEngine()
    script = engine.load_script(nf_file)
    return engine.execute(script, executor=executor, params=params, input_files=input_files)
```

## 5. **Usage Examples**

**Basic Usage:**
```python
from py_nf import NextflowEngine

engine = NextflowEngine()
script = engine.load_script("basic.nf")
results = engine.execute(script, params={"in": "data/sample.fa"})

print(f"Output files: {results.get_output_files()}")
print(f"Execution report: {results.get_execution_report()}")
```

**Multiple Input Files:**
```python
results = engine.execute(script, input_files=["file1.txt", "file2.txt"])
```

**Slurm Execution:**
```python
results = engine.execute(script, executor="slurm",
                        config={"queue": "normal", "time": "1h"})
```

**One-liner:**
```python
from py_nf import run_workflow
results = run_workflow("workflow.nf", params={"input": "data.txt"})
```

## 6. **Implementation Steps**
1. Set up Python package structure
2. Implement `NextflowEngine` with JPype integration
3. Implement `NextflowResult` for output handling
4. Create public API with convenience functions
5. Add comprehensive error handling and logging
6. Write tests using sample `.nf` files from `nextflow/tests/`

This approach provides a clean Python interface while leveraging 100% of Nextflow's existing, battle-tested infrastructure through direct JVM integration.