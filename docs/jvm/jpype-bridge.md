# JPype bridge (Python ↔ JVM)

`pynf` embeds the Nextflow engine in-process via **JPype**.

## What “embedding Nextflow” means

- We start a JVM once per Python process.
- We add the Nextflow **fat JAR** to the classpath.
- We directly call Nextflow Java classes (`jpype.JClass("...")`) instead of spawning `nextflow run` as a subprocess.

This gives:
- lower overhead per run
- structured access to runtime objects for introspection
- a clean “Python function returns result” ergonomics

## JVM lifecycle

In `_core/execution.py`:
- `resolve_nextflow_jar_path(...)` decides which JAR to use
- `start_jvm_if_needed(jar_path)` starts the JVM only if it is not running

Important constraints:
- JPype cannot safely “restart” the JVM in the same process; treat JVM start as one-way.
- The classpath is effectively fixed at JVM start.

## Loading Nextflow classes

We load the core classes with `jpype.JClass`.

### Classes we rely on

- `nextflow.Session`
- `nextflow.script.ScriptLoaderFactory`
- `nextflow.script.ScriptMeta`
- `nextflow.trace.TraceObserverV2`

These names are intentionally included verbatim because they are the anchor points for debugging.

## Python → Java value conversion

When binding user inputs into Nextflow parameters, we coerce Python values to Java-friendly types.

In `_core/execution.py`:
- dict-like values become `java.util.HashMap`
- list-like values become `java.util.ArrayList`
- `path` values become strings

This is implemented by `to_java(...)`.

## Java → Python conversion

Nextflow workflow outputs can be Java collections.

In `_core/result.py`, `to_python(...)`:
- converts map-like objects via `.entrySet().iterator()`
- converts iterable-like objects via `.iterator()`
- falls back to string representation when needed

## Excerpt: observer registration via reflection

Nextflow keeps observer lists as internal fields. We attach our `TraceObserverV2` proxy by mutating an internal field.

Code excerpt (field name is important):

```python
field = session.getClass().getDeclaredField("observersV2")
field.setAccessible(True)
observers = field.get(session)
observers.add(observer_proxy)
```

This is intentionally documented because if Nextflow changes the field name, output capture will break.
