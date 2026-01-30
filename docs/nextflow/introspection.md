# Nextflow introspection (process inputs)

`pynf` introspects process inputs to validate user-supplied inputs and to power the CLI `list-inputs` command.

## Where introspection happens

- Script parsing happens in `_core/execution.execute_nextflow`.
- For nf-core modules, introspection is also used in `_core/nfcore_modules.get_module_inputs`.

## The ScriptMeta path

We use the Nextflow `ScriptMeta` API:

1. `script_meta = ScriptMeta.get(script)`
2. enumerate processes (`getProcessNames()` / `getProcess(...)`)
3. from each process:
   - `process_def.getProcessConfig()`
   - `process_config.getInputs()`

Each input definition yields:
- channel type (`getTypeName()`)
- parameter names (`getName()`)

## Module mode toggling

In some cases, a script may not expose process metadata until it is executed.
We toggle module mode and run the script to force metadata population.

Excerpt (conceptual):

```python
script_loader.setModule(True)
script_meta = ScriptMeta.get(script)
process_names = script_meta.getProcessNames()

if not process_names:
    script_loader.runScript()
    process_names = script_meta.getProcessNames()
```

## Output format

We normalize input definitions into Python dictionaries like:

```json
{
  "type": "tuple",
  "params": [
    {"type": "val", "name": "meta"},
    {"type": "path", "name": "reads"}
  ]
}
```
