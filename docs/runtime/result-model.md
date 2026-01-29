# Result model and output discovery

The Python-side return value for an execution is `NextflowResult`.

## Why the result is event-based

We avoid holding on to live JVM objects because:
- the Nextflow `Session` is destroyed at the end of each run
- JPype proxies can become invalid after teardown

Instead, we capture:
- workflow output events
- file publish events
- task work directories
- a snapshot execution report

## Execution report snapshot

Before destroying the session we snapshot:
- `work_dir`
- succeeded task count
- failed task count

## Output file discovery

`NextflowResult.get_output_files()`:

1. Prefer observer-derived paths:
   - workflow output values (flattened)
   - file publish targets

2. Fallback to scanning captured task workdirs:
   - list non-hidden files in each work directory

## Java→Python normalization

Workflow outputs may be Java collections.

`to_python(...)` converts:
- Map-like objects via `.entrySet().iterator()`
- Iterable-like objects via `.iterator()`

Values that can’t be converted cleanly fall back to `str(value)`.
