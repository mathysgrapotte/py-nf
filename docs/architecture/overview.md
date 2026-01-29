# Architecture overview

`pynf` is intentionally organized around a small public surface and an internal implementation package.

## Public surface

- `pynf/__init__.py`
  - “Functional-first” convenience wrappers.
  - Intended for interactive / quick usage.

- `pynf/api.py`
  - Canonical programmatic entry points.
  - Thin composition layer that delegates to `_core`.

- `pynf/cli.py`
  - CLI wiring (`pynf` command).
  - Calls public API functions; contains no core runtime logic.

## Internal implementation (`pynf/_core`)

- `_core/execution.py`
  - Embedded Nextflow runtime via JPype.
  - Responsibilities:
    - resolve JAR path, start JVM
    - initialize and run a Nextflow `Session`
    - validate/coerce inputs to Java values
    - register an observer and collect events
    - snapshot a stable `NextflowResult`

- `_core/result.py`
  - Stable event-based result model.
  - Responsibilities:
    - normalize Java values → JSON-ish Python values
    - extract output file paths from observer events
    - provide a minimal set of convenience accessors

- `_core/nfcore_modules.py`
  - nf-core module catalog + caching + orchestration.
  - Responsibilities:
    - define module-id semantics
    - list modules/submodules via GitHub
    - download/cache `main.nf` + `meta.yml`
    - run and introspect modules by invoking `_core.execution`

- `_core/github_api.py`
  - Single IO boundary to GitHub HTTP calls.

- `_core/types.py`
  - Dataclasses and type aliases (`ExecutionRequest`, `DockerConfig`, `ModulePaths`, etc.).

- `_core/validation.py`
  - Pure validation helpers for user inputs.

## Design invariants

- The public surface remains **functional**.
- `_core` modules may be refactored freely as long as `pynf.api` stays stable.
- `NextflowResult` is **event-based** (no live JVM objects are stored).
