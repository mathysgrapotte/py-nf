# Nextflow internals primer (as used by py-nf)

This is not a full Nextflow architecture doc. It’s the minimal internal model needed to debug `pynf`.

## Key objects

### `nextflow.Session`

A Session holds:
- configuration (`session.getConfig()`)
- working directory (`session.getWorkDir()`)
- observers (including `observersV2`)
- lifecycle state for one execution

In our code, the core lifecycle is:

1. `session.init(script_file, args, ...)`
2. `session.start()`
3. `loader.runScript()`
4. `session.fireDataflowNetwork(False)`
5. `session.await_()`
6. `session.destroy()`

### Script loader

We create the loader via:

- `nextflow.script.ScriptLoaderFactory.create(session)`

Then:
- `loader.parse(path)` parses the script
- `loader.getScript()` returns a Script object

### `nextflow.script.ScriptMeta`

We use `ScriptMeta` for introspection:
- `ScriptMeta.get(script)` returns metadata
- we enumerate process definitions
- we read input definitions from each process config

## Why we call `fireDataflowNetwork(False)`

After `loader.runScript()`, Nextflow’s network may need an explicit trigger. `fireDataflowNetwork(False)` ensures the graph is started.

## Why we call `await_()`

`await_()` blocks until the run completes.

## What we snapshot

Before teardown, we snapshot:
- `workDir`
- succeeded/failed task counts
- observer-collected events

This produces a stable Python-side `NextflowResult`.
