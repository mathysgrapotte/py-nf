# Nextflow Runtime Notes

Collected while wiring Python bindings to the embedded Nextflow sources (`nextflow/modules/nextflow`).

## Session lifecycle
- `nextflow.Session` owns execution state (work dir, output dir, observers, workflow metadata, etc.).
- During `Session.init(...)` it creates both *trace observer* lists: legacy `TraceObserver` (`observersV1`) and modern `TraceObserverV2` (`observersV2`).
- `observersV2` always contains a `WorkflowStatsObserver` by default; additional observers are added via `Plugins.getExtensions(TraceObserverFactoryV2)`.
- The session exposes notification hooks (e.g. `notifyFlowCreate`, `notifyTask[Start|Complete]`, `notifyWorkflowOutput`, `notifyFilePublish`, `notifyFlowComplete`) that fan out to all registered observers.
- Observer lists are stored as private fields; they can be mutated via reflection (needed for JPype proxies).

## TraceObserverV2 contract
- Defined in `nextflow/trace/TraceObserverV2.groovy`.
- Provides lifecycle callbacks for flows, processes, tasks, published files, and workflow outputs.
- `onWorkflowOutput(WorkflowOutputEvent event)` is triggered after a publish operator finishes.
- `onFilePublish(FilePublishEvent event)` fires for any file publication (either from `publishDir` or workflow outputs/index files).

## Workflow output signalling
- `PublishOp` (`nextflow/extension/PublishOp.groovy`) calls `session.notifyWorkflowOutput(new WorkflowOutputEvent(...))` when a workflow output completes.
- The same operator notifies file publications via `session.notifyFilePublish(new FilePublishEvent(...))`, including optional label metadata.

## Event payloads
- `WorkflowOutputEvent` (in `nextflow/trace/event/WorkflowOutputEvent.groovy`):
  - `name` — logical output name
  - `value` — output value (may be a file path, collection, map, etc.). Null when an index file is emitted instead.
  - `index` — optional `Path` to the generated index artifact (CSV/JSON/YAML).
- `FilePublishEvent` (in `nextflow/trace/event/FilePublishEvent.groovy`):
  - `source` — original work-dir path (may be null for workflow-level outputs)
  - `target` — final published path
  - `labels` — list of `publishDir` labels applied to the file.

## Work-dir structure
- Session initializes `workDir` and `outputDir` (`FileHelper.toCanonicalPath(...)`) early in `create(config)`.
- `PublishOp.getTaskDir(...)` attempts to map absolute paths back to their task directory (e.g., `work/ab/cdef...`), supporting staging and normalization logic.

## Reflection helper hints
- `Session` keeps observers in private fields `observersV1` and `observersV2`; accessing them from JPype requires `session.getClass().getDeclaredField("observersV2")` followed by `setAccessible(true)`.
- Fields are Java `List` implementations; append/remove with `.add()` / `.remove()`.

## Event ordering expectations
- `notifyWorkflowOutput` and `notifyFilePublish` are called before `notifyFlowComplete`.
- Workflow completion runs shutdown hooks (`onShutdown`) and triggers all observers’ `onFlowComplete()` once barriers resolve.

## Useful classes to import via JPype
- `nextflow.Session`
- `nextflow.trace.TraceObserverV2`
- `nextflow.script.ScriptLoaderFactory`
- `nextflow.script.ScriptFile`
- `java.util.ArrayList`
- Event payload classes if direct inspection is needed (`nextflow.trace.event.WorkflowOutputEvent`, `FilePublishEvent`).
