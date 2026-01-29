# py-nf developer documentation

This folder is a *developer-focused* description of how `pynf` works internally.

## Reading order

1. [`architecture/overview.md`](architecture/overview.md)
2. [`architecture/call-graph.md`](architecture/call-graph.md)
3. [`jvm/jpype-bridge.md`](jvm/jpype-bridge.md)
4. [`nextflow/internals-primer.md`](nextflow/internals-primer.md)
5. [`nextflow/introspection.md`](nextflow/introspection.md)
6. [`nextflow/observers-and-events.md`](nextflow/observers-and-events.md)
7. [`runtime/result-model.md`](runtime/result-model.md)
8. [`nfcore/modules-cache.md`](nfcore/modules-cache.md)
9. [`traces/end-to-end.md`](traces/end-to-end.md)

## Glossary (quick)

- **Nextflow fat JAR**: the single JAR containing the Nextflow runtime + dependencies. Added to JVM classpath.
- **Session (`nextflow.Session`)**: the core runtime object that holds config, work dir, observers, and orchestrates execution.
- **Script loader**: parses and runs a Nextflow script (`nextflow.script.ScriptLoaderFactory`).
- **ScriptMeta**: Nextflow metadata API used for introspection (`nextflow.script.ScriptMeta`).
- **TraceObserverV2**: observer interface used to capture workflow outputs and file publish events.
- **workDir**: Nextflow session working directory where task directories are created.
