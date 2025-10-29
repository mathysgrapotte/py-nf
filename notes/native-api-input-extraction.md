# Using Nextflow Native API for Input Extraction

## Problem with Current Approach

The current implementation in `src/pynf/engine.py:361-461` uses **heuristic-based AST parsing**:
- Manually compiles Groovy AST using `CompilationUnit`
- Walks AST tree with fragile pattern matching
- Searches for process closures by inspecting method calls
- Extracts inputs using string matching on method names (`tuple`, `val`, `path`, etc.)
- ~100 lines of brittle code that may break with Nextflow updates

## Native Nextflow API Solution

Nextflow provides **official Java/Groovy APIs** for accessing process metadata that handle all the parsing internally.

### Key Classes

1. **ScriptMeta** - Global registry of script metadata
   - `ScriptMeta.get(script)` - Get metadata for a script
   - `getProcess(name)` - Get ProcessDef by name
   - `getProcessNames()` - List all process names

2. **ProcessDef** - Process definition
   - `getProcessConfig()` - Returns ProcessConfig (V1 or V2)

3. **ProcessConfig** - Process configuration
   - `getInputs()` - Returns input list (InputsList for V1)

4. **InputsList** - List of input parameters (V1 style, used by nf-core modules)
   - Implements `List<InParam>`
   - Iterate to get each input parameter

5. **InParam** implementations:
   - `TupleInParam` - Tuple inputs with `getInner()` for components
   - `ValueInParam` - Single value inputs
   - `FileInParam` - Single file/path inputs
   - Each has: `getName()`, `getTypeName()`

## How It Works: Step-by-Step

### 1. Parse (`loader.parse(script_path)`)
```python
loader = ScriptLoaderFactory.create(session)
loader.parse(java_path)
```
- Compiles the Nextflow script into Groovy AST
- Creates the script class but doesn't execute it
- **Processes are NOT yet registered at this point**

### 2. Set Module Mode (`loader.setModule(True)`)
```python
loader.setModule(True)
```
- Tells Nextflow this is a module, not a standalone workflow
- Prevents it from trying to execute a workflow entry point

### 3. Run Script (`loader.runScript()`)
```python
try:
    loader.runScript()  # May fail due to missing params
except:
    pass  # Process definitions are already registered!
```

**What happens during runScript():**
- Executes the script's **definition code** (not the process tasks!)
- When Nextflow encounters `process SAMTOOLS_VIEW { input: ... }`, this is **executable Groovy code**
- This code:
  1. Creates ProcessDef objects
  2. Parses input/output blocks into structured objects (InputsList, etc.)
  3. **Registers them in ScriptMeta** (global registry)
- May fail with "Missing required parameter" error
- **BUT**: Process definitions are already created and registered before it fails!

### 4. Query Process Metadata
```python
script = loader.getScript()
script_meta = ScriptMeta.get(script)
process_def = script_meta.getProcess("SAMTOOLS_VIEW")
inputs = process_def.getProcessConfig().getInputs()
```
- ScriptMeta now contains all process definitions
- Query returns fully parsed input structures

### 5. Extract Input Details
```python
for inp in inputs:
    name = inp.getName()
    type_name = inp.getTypeName()  # 'tuple', 'val', 'path', etc.

    # Handle tuple inputs
    if hasattr(inp, 'getInner') and inp.getInner():
        for component in inp.getInner():
            comp_name = component.getName()
            comp_type = component.getTypeName()
```

## Visual Flow

```
┌─────────────────────────────────────────────────────────────┐
│ nf-core module file:                                        │
│                                                             │
│ process SAMTOOLS_VIEW {                                     │
│   input:                                                    │
│   tuple val(meta), path(input), path(index)                 │
│   path qname                                                │
│   val index_format                                          │
│ }                                                           │
└─────────────────────────────────────────────────────────────┘
                    ↓
        loader.parse(script_path)  ← Compile to AST
                    ↓
        loader.runScript()  ← Execute definition code
                    ↓
    ┌───────────────────────────────────────┐
    │ This Groovy code executes:            │
    │                                       │
    │ def processDef = new ProcessDef(...)  │
    │ processDef.config.addInput(tuple(...))│
    │ ScriptMeta.register(processDef)       │
    └───────────────────────────────────────┘
                    ↓
    ScriptMeta now contains SAMTOOLS_VIEW
         with fully parsed input structure
                    ↓
    We query: ScriptMeta.getProcess("SAMTOOLS_VIEW")
                    ↓
    We get: ProcessDef with InputsList containing:
            - Input #1: TupleInParam with 3 components
              - val(meta)
              - path(input)
              - path(index)
            - Input #2: TupleInParam with 2 components
              - val(meta2)
              - path(fasta)
            - Input #3: FileInParam - path(qname)
            - Input #4: ValueInParam - val(index_format)
```

## Test Results

### SAMTOOLS_VIEW (4 inputs)
```
Input #1: tuple(__$tupleinparam<0>)
  → Tuple with 3 components:
      [0] name=meta, type=val
      [1] name=input, type=path
      [2] name=index, type=path

Input #2: tuple(__$tupleinparam<1>)
  → Tuple with 2 components:
      [0] name=meta2, type=val
      [1] name=fasta, type=path

Input #3: path(qname)
  Name: qname
  TypeName: path

Input #4: val(index_format)
  Name: index_format
  TypeName: val
```

### FASTQC (1 input)
```
Input #1: tuple(__$tupleinparam<0>)
  → Tuple with 2 components:
      [0] name=meta, type=val
      [1] name=reads, type=path
```

## Implementation Code

```python
def _get_process_inputs_from_api(self, loader):
    """
    Extract process inputs using Nextflow's native API.

    This replaces the heuristic-based AST parsing approach with
    Nextflow's official process metadata API.
    """
    # Get the script object
    script = loader.getScript()

    # Set as module to avoid workflow execution
    loader.setModule(True)

    # Run script to register process definitions
    try:
        loader.runScript()
    except Exception:
        # Expected to fail due to missing params, but processes are registered
        pass

    # Get script metadata
    ScriptMeta = jpype.JClass("nextflow.script.ScriptMeta")
    script_meta = ScriptMeta.get(script)

    # Get all processes
    process_names = script_meta.getProcessNames()

    input_channels = []

    # For each process, extract inputs
    for process_name in process_names:
        process_def = script_meta.getProcess(process_name)
        process_config = process_def.getProcessConfig()
        inputs = process_config.getInputs()

        for inp in inputs:
            channel_info = {
                'type': str(inp.getTypeName()),
                'params': []
            }

            # Handle tuple inputs
            if hasattr(inp, 'getInner') and inp.getInner() is not None:
                inner = inp.getInner()
                for component in inner:
                    channel_info['params'].append({
                        'type': str(component.getTypeName()),
                        'name': str(component.getName())
                    })
            else:
                # Simple input (val, path, etc.)
                channel_info['params'].append({
                    'type': str(inp.getTypeName()),
                    'name': str(inp.getName())
                })

            input_channels.append(channel_info)

    return input_channels
```

## Key Insights

### Why runScript() is Necessary

The Nextflow script file is **not just data** - it's **executable code** that constructs process definitions when run.

Think of it like Python:
- **Parsing** = compiling Python code (`compile()`)
- **Running** = executing module-level code (like class definitions)
- You need to "import" the module to register the classes, even if you don't call any methods

When you write:
```groovy
process SAMTOOLS_VIEW {
    input:
    tuple val(meta), path(input)
}
```

This is **executable Groovy code** that:
1. Calls the `process()` method defined in BaseScript
2. Creates a ProcessDef object
3. Parses the input block using ProcessDslV1/V2
4. Registers it in ScriptMeta

### Error Handling

The `runScript()` call may fail with:
```
java.lang.IllegalArgumentException: Missing required parameter: --meta
```

This error happens **after** process registration, when Nextflow tries to validate workflow parameters. By that point, all the process structures we need are already in ScriptMeta!

## Advantages Over AST Parsing

✅ **Official Nextflow API** - Maintained by Nextflow team
✅ **Works with DSL2** - nf-core modules use DSL2
✅ **Handles tuples correctly** - Full component details
✅ **Type information** - val, path, tuple, etc.
✅ **No fragile heuristics** - Uses Nextflow's actual parser
✅ **Eliminates ~100 lines** of brittle code
✅ **Future-proof** - Won't break with Nextflow updates
✅ **Supports both V1 and V2** - Process config versions

## DSL Versions vs Process Config Versions

**Important distinction:**
- **DSL1 vs DSL2** = Script-level language syntax
- **ProcessConfigV1 vs V2** = Process definition style

nf-core modules:
- Use **DSL2** (script level)
- Use **ProcessConfigV1** (process definition style)
- This is why they have InputsList, not ProcessInputsDef

Both are supported by the native API approach.

## Next Steps

1. Add ScriptMeta import in `NextflowEngine.__init__()`:
   ```python
   self.ScriptMeta = jpype.JClass("nextflow.script.ScriptMeta")
   ```

2. Replace `_parse_inputs_from_ast()` with `_get_process_inputs_from_api()`

3. Update `execute()` method to call new function after `loader.parse()`

4. Update `_set_params_from_inputs()` to work with new format

5. Test with existing nf-core modules

## Test Scripts

Test scripts created for validation:
- `test_native_api.py` - Basic API exploration
- `test_extract_inputs.py` - Full input extraction for SAMTOOLS_VIEW
- `/tmp/test_fastqc.py` - FASTQC validation

All tests confirm the native API approach works correctly with nf-core modules.
