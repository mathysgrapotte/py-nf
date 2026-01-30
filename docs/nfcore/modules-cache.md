# nf-core modules: ids, catalog, caching

This document describes the nf-core integration from the developer perspective.

## Canonical ModuleId

Canonical module ids are **relative to** `modules/nf-core/` in the nf-core/modules repository.

Examples:
- `fastqc`
- `samtools/view`

At the boundary we accept `nf-core/<id>` and normalize it away.

Implementation: `_core/nfcore_modules.normalize_module_id`.

## Cache layout

On disk:

```text
<cache_dir>/
  modules_list.txt
  fastqc/
    main.nf
    meta.yml
  samtools/view/
    main.nf
    meta.yml
```

`modules_list.txt` is a cached list of top-level module names.

## GitHub endpoints used

- Contents API:
  - `https://api.github.com/repos/nf-core/modules/contents/modules/nf-core`
- Raw file fetch:
  - `https://raw.githubusercontent.com/nf-core/modules/master/modules/nf-core/<module>/main.nf`
  - `https://raw.githubusercontent.com/nf-core/modules/master/modules/nf-core/<module>/meta.yml`

All HTTP is centralized in `_core/github_api.py`.

## Orchestration

- `ensure_module(...)` downloads and writes `main.nf` + `meta.yml`.
- `run_nfcore_module(...)`:
  - calls `ensure_module(...)`
  - builds a new `ExecutionRequest` with `script_path = cached main.nf`
  - calls `_core.execution.execute_nextflow(...)`

## Notes on `meta.yml`

We currently download and store `meta.yml` primarily for inspection / debugging.
The runtime input validation is based on Nextflow introspection rather than parsing `meta.yml`.
