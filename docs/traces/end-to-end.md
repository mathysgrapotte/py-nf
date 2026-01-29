# End-to-end traces (developer)

This page is meant to be read while stepping through the code in a debugger.

## Trace: run an nf-core module

Starting from user code:

```python
from pathlib import Path
from pynf import ExecutionRequest, run_nfcore_module

req = ExecutionRequest(script_path=Path("."), inputs=[{"meta": {"id": "s1"}, "reads": ["a.fastq"]}])
res = run_nfcore_module("fastqc", req)
```

Call chain:

1. `pynf.run_nfcore_module` (wrapper)
2. `pynf.api.run_module`
3. `_core.nfcore_modules.run_nfcore_module`
   - `ensure_module(...)`
   - build `module_request` with `script_path = cached main.nf`
4. `_core.execution.execute_nextflow`
   - resolve jar
   - start JVM
   - init + start Session
   - parse script
   - validate inputs + `to_java` coercion
   - register observer (`observersV2`)
   - run + await
   - snapshot report + events
5. `_core.result.NextflowResult` methods:
   - `get_output_files()` (events -> publish -> workdir fallback)
   - `get_workflow_outputs()` (Java -> Python)

## Trace: introspect inputs

1. `pynf.api.get_module_inputs`
2. `_core.nfcore_modules.get_module_inputs`
3. `_core.execution.load_nextflow_classes` + Session init/start
4. `_core.execution.get_process_inputs`

## Suggested debug breakpoints

- `_core.execution.execute_nextflow`
- `_core.execution.registered_trace_observer` (observer attach)
- `_core.execution.get_process_inputs`
- `_core.nfcore_modules.ensure_module`
- `_core.result.NextflowResult.get_output_files`
