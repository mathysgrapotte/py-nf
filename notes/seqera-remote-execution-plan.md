# Plan: Remote execution via Seqera Platform (Tower) API for `py-nf`

Branch: `remove-nextflowengine`

Goal: keep the current “seamless py-nf” UX (Python call returns a result object) while allowing **remote execution on a Seqera Platform compute environment**, instead of running a local embedded Nextflow JVM.

---

## 0) Current architecture (as of this branch)

### Local embedded engine
- `pynf.api.run_module(...)` downloads/caches an nf-core module and then calls `pynf.execution.execute_nextflow(request)`.
- `execute_nextflow()` uses JPype to start a JVM and load Nextflow classes from a fat JAR:
  - `start_jvm_if_needed(jar_path)`
  - `load_nextflow_classes()` → `nextflow.Session`, `nextflow.script.ScriptLoaderFactory`, etc.
- It parses the module `main.nf`, introspects inputs (`process_introspection.get_process_inputs`), sets `session.params`, then runs the script in-process:
  - `loader.runScript(); session.fireDataflowNetwork(False); session.await_()`
- Output collection is done via TraceObserverV2 proxy `WorkflowOutputCollector`.

### Key implication
This code path is **necessarily local**: it requires a Nextflow JAR and a JVM on the client machine.

---

## 1) Desired behavior

Expose a remote backend so users can do something like:

```py
from pynf import run_module
from pynf.types import ExecutionRequest

req = ExecutionRequest(..., backend="seqera", seqera=...)
result = run_module("fastqc", req)
```

Where `result` behaves similarly to local execution, but the workflow is **submitted to Seqera Platform** and executed in a selected **compute environment**.

Two non-goals (for v1):
- full feature parity with local TraceObserver-based event capture
- streaming live task events

---

## 2) Seqera Platform API capability (what we’ll use)

Seqera Platform exposes an OpenAPI spec at:
- https://cloud.seqera.io/openapi/seqera-api-latest.yml

Relevant endpoint:
- `POST https://api.cloud.seqera.io/workflow/launch?workspaceId=<int>`
  - operationId: `CreateWorkflowLaunch`

Request schema:
- `SubmitWorkflowLaunchRequest { launch: WorkflowLaunchRequest }`

`WorkflowLaunchRequest` supports (among others):
- `computeEnvId` (string)
- `pipeline` (string) OR `mainScript` (string)
- `revision`, `runName`
- `workDir`
- `configText`, `paramsText`
- `entryName`

This makes a “no repo needed” approach feasible: we can submit `mainScript` directly.

---

## 3) Implementation plan (minimal viable)

### 3.1 Add a backend switch
Add a notion of execution backend:
- default: `local` (current JPype path)
- new: `seqera`

Where to put it:
- Add fields to `pynf.types.ExecutionRequest`:
  - `backend: Literal["local","seqera"] = "local"`
  - `seqera: SeqeraConfig | None = None`

New `SeqeraConfig` (dataclass / pydantic-like simple class) includes:
- `access_token: str` (or read from env `TOWER_ACCESS_TOKEN`)
- `api_endpoint: str = "https://api.cloud.seqera.io"` (or env `TOWER_API_ENDPOINT`)
- `workspace_id: int`
- `compute_env_id: str`
- optional: `work_dir: str` (e.g. `s3://bucket/pynf-work`)
- optional: `run_name: str`

### 3.2 Implement `execute_seqera(request)`
New module `pynf/seqera_client.py`:
- thin HTTP client using `requests` (already used in repo for GitHub)
- methods:
  - `create_workflow_launch(...) -> workflowId`
  - `get_workflow(workflowId) -> status + metadata` (endpoint to confirm from OpenAPI)
  - `wait_workflow(workflowId, terminal_states={SUCCEEDED,FAILED}, poll=10s)`

### 3.3 Build a script to submit (`mainScript`)
We have two options:

**Option A (fastest): submit the nf-core module `main.nf` as `mainScript`**
- Pros: minimal extra code
- Cons: nf-core modules are usually DSL2 modules (not full runnable pipelines). They often require being included from a parent workflow.

**Option B (recommended): generate a tiny wrapper workflow (DSL2) that includes the module and wires channels**
- This matches the “run module” mental model.
- `py-nf` already introspects module inputs; we can use that to generate minimal channel creation code.

For v1, I propose:
- Generate a wrapper `mainScript` that:
  - `include { <process> } from '<path or module include>'` (depending on how modules are structured in cache)
  - creates input channels from `params` / `inputs`
  - calls the module process
  - publishes outputs to a known `publishDir` (preferably under `launch.workDir` or an explicit `outDir` param)

We will store this wrapper script as text and submit via `WorkflowLaunchRequest.mainScript`.

### 3.4 Provide config/params to the remote run
- `WorkflowLaunchRequest.paramsText`: encode the request parameters in Nextflow config syntax (YAML/JSON supported per Seqera CLI docs; Platform accepts text)
- `WorkflowLaunchRequest.configText`: inject things like:
  - `manifest` (optional)
  - `process.container` / `docker.enabled` / `wave` settings depending on compute env

Important: remote CE usually requires containerization (AWS Batch/K8s). For HPC, it may rely on environment modules/conda.
We should not hardcode containers; just allow passing config.

---

## 4) Result object shape for remote runs

Current result: `pynf.result.NextflowResult` wraps local JVM objects.
Remote execution cannot return those.

Plan:
- Add `pynf.result.SeqeraResult` implementing a compatible surface:
  - `get_execution_report()` → dict (status, runName, workflowId, timestamps, url)
  - `get_output_files()` → list[str] of output URIs (best effort)
  - `get_task_workdirs()` → list[str] (likely unavailable; return [])

We can also add:
- `result.url` (watch URL)
- `result.workflow_id`

---

## 5) What we still need to confirm (before coding)

1. Which API endpoints to poll for workflow status and retrieve outputs.
   - From OpenAPI: there are `workflows` and `trace` tags; we need the exact paths.

2. How to represent outputs reliably.
   - Easiest: force `publishDir` to an S3 prefix and return those objects.

3. Authentication + permissions.
   - Require Bearer token (`TOWER_ACCESS_TOKEN`) + workspace access.

4. Whether Seqera accepts `mainScript` for module wrapper scripts in all scenarios.

---

## 6) Suggested UX additions

- `backend="seqera"` in `ExecutionRequest`
- env var support:
  - `TOWER_ACCESS_TOKEN`
  - `TOWER_API_ENDPOINT`
  - `TOWER_WORKSPACE_ID`
  - `TOWER_COMPUTE_ENV_ID`

- Convenience function:
  - `pynf.seqera.run_module_remote(module_id, request, compute_env_id=..., workspace_id=...)`

---

## 7) Minimal example (target)

```py
from pynf import api
from pynf.types import ExecutionRequest, SeqeraConfig

req = ExecutionRequest(
    script_path=None,  # ignored for modules
    params={"outdir": "s3://my-bucket/pynf-out/run-123"},
    inputs=[{"meta": {"id": "sample1"}, "reads": "s3://.../R1.fastq.gz"}],
    backend="seqera",
    seqera=SeqeraConfig(
        workspace_id=123,
        compute_env_id="1abcDEF...",
        work_dir="s3://my-bucket/pynf-work",
        access_token=os.environ["TOWER_ACCESS_TOKEN"],
    ),
)

result = api.run_module("fastqc", req)
print(result.get_execution_report())
```

---

## 8) Next steps

- [ ] Confirm polling endpoint for workflow status in OpenAPI spec
- [ ] Implement `SeqeraClient` + minimal `execute_seqera()`
- [ ] Implement `SeqeraResult`
- [ ] Add backend switch in `execute_nextflow` dispatcher
- [ ] Add docs + examples
