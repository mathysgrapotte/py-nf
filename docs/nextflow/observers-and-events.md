# Observers and runtime events

`pynf` captures runtime signals from Nextflow via the `TraceObserverV2` interface.

## The interface

We create a Python object (`WorkflowOutputCollector`) and expose it to Nextflow as a Java interface via:

- `jpype.JProxy(TraceObserverV2, inst=collector)`

## Events we use

### Workflow outputs

`onWorkflowOutput(event)`
- Captures named workflow outputs.
- We store the raw Java value and convert it later in `NextflowResult`.

### File publish events

`onFilePublish(event)`
- Captures publish events (target/source/labels).
- Used for `get_output_files()`.

### Task work directories

`onTaskComplete(event)` and `onTaskCached(event)`
- We capture `task.getWorkDir()`.
- Used as a fallback output discovery mechanism.

## Internal hook: observers list

We attach our observer by mutating an internal field on `Session`:

- field name: `observersV2`

This is a brittle but practical integration point.

## Failure modes

- If Nextflow changes the internal observer field name or type, event capture can break.
- If the observer cannot be registered, `NextflowResult` may still exist but output file discovery may fall back to workdir scanning only.
