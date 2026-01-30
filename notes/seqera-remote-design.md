# Seqera Remote Execution Design (py-nf)

## Goals
- Add a minimal Seqera Platform backend using the public OpenAPI.
- Keep the local JPype execution path unchanged.
- Require `params["outdir"]` for remote runs so outputs are deterministic.

## Non-goals (v1)
- No streaming task events or trace ingestion.
- No output enumeration beyond the supplied outdir.
- No support for advanced launch fields (secrets, labels, profiles, etc.).

## Architecture changes
- `template/pynf/_core/types.pyi` + `src/pynf/_core/types.py`
  - Add `ExecutionBackend` (`local` or `seqera`).
  - Add `SeqeraConfig` (token, endpoint, workspace/compute env, work_dir/run_name).
  - Extend `ExecutionRequest` with `backend` and `seqera`.
- `template/pynf/_core/result.pyi` + `src/pynf/_core/result.py`
  - Add `SeqeraResult` (workflow id, status, url, outdir).
- `template/pynf/_core/seqera_client.pyi` + `src/pynf/_core/seqera_client.py`
  - Small HTTP client for `/workflow/launch` and `/workflow/{id}`.
- `template/pynf/_core/seqera_execution.pyi` + `src/pynf/_core/seqera_execution.py`
  - Build wrapper workflows for nf-core modules.
  - Submit and poll remote executions.
- `template/pynf/_core/execution.pyi` + `src/pynf/_core/execution.py`
  - Add `execute_request` dispatcher; local path unchanged.
- `src/pynf/api.py`
  - `run_script` now dispatches via `execute_request`.
- `src/pynf/_core/nfcore_modules.py`
  - `run_nfcore_module` uses `execute_seqera_module` when `backend="seqera"`.
- `template/pynf/__init__.pyi` + `src/pynf/__init__.py`
  - Export `SeqeraConfig` and `SeqeraResult` and document remote returns.

## Remote execution flow
1. `ExecutionRequest.backend == "seqera"` triggers the remote path.
2. Enforce `params["outdir"]` (required).
3. Build `paramsText` from request params + inputs (JSON).
4. For modules, generate a DSL2 wrapper script that:
   - embeds the module process
   - wires `params.inputs` into channels
   - applies `publishDir` using `params.outdir`
5. Submit to `POST /workflow/launch?workspaceId=...` with:
   - `computeEnvId`, `mainScript`, `paramsText`, optional `workDir` + `runName`
6. Poll `GET /workflow/{workflowId}` until status is terminal.
7. Return `SeqeraResult` with status, workflow id, and outdir pointer.

## Outdir requirement
- `params["outdir"]` is required for remote runs.
- Used both for `publishDir` and the minimal output reference in `SeqeraResult`.

## OpenAPI-only fields used
- `computeEnvId`
- `mainScript`
- `paramsText`
- `workDir` (optional)
- `runName` (optional)
