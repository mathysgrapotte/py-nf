# Module Chaining Implementation Plan

## Problem Statement

Currently, pynf can only execute single modules in isolation. There's no way to chain multiple Nextflow modules together where the output of one module becomes the input to the next. This limits the ability to build complex bioinformatics pipelines programmatically from Python.

## Goals

1. **Enable sequential module execution** - Run module A, then module B using A's outputs
2. **Pythonic API** - Feel natural in notebooks and interactive Python sessions
3. **Explicit data flow** - Clear visibility into what data moves between modules
4. **Clean isolation** - Each module runs in its own session (avoid state contamination)
5. **Inspectable** - Users can examine intermediate results between steps
6. **Backward compatible** - Don't break existing `run_module()` usage

## Design Decision: Explicit Channel Passing

After analyzing the options, we'll implement **explicit channel passing** because:

- **Most Pythonic**: Clear, readable code that follows Python conventions
- **Notebook-friendly**: Each step is independent and results can be inspected
- **Debuggable**: Easy to print/examine intermediate outputs
- **Flexible**: Simple to branch, filter, or transform data between modules
- **Clean**: New session per module = no complex state management

Example of desired API:
```python
# Basic chaining
result1 = run_module("fastqc.nf", inputs=[{"reads": "sample.fastq"}])
result2 = run_module("trimming.nf", inputs=result1.to_inputs())

# Convenience wrapper
from pynf import chain
results = chain(
    ("fastqc.nf", [{"reads": "sample.fastq"}]),
    ("trimming.nf", {}),  # Uses previous outputs
    ("alignment.nf", {"reference": "ref.fa"})  # Mix outputs + new params
)
```

## Implementation Plan

### Phase 1: Enhance NextflowResult (src/pynf/result.py)

**Goal**: Make NextflowResult outputs easily consumable as inputs for next module.

#### 1.1 Add `to_inputs()` method
```python
def to_inputs(self, channel_mapping=None):
    """
    Convert workflow outputs to input format for next module.

    Args:
        channel_mapping: Optional dict to map output names to input names
                        e.g., {"fastqc_html": "qc_report"}

    Returns:
        List of input dicts suitable for engine.execute(inputs=...)

    Example:
        result1 = run_module("fastqc.nf", ...)
        result2 = run_module("trimming.nf", inputs=result1.to_inputs())
    """
```

**Implementation details**:
- Extract values from `self._workflow_events` (already captured by observer)
- Handle different output types: files (paths), values (strings/numbers), tuples
- Convert Java objects to Python equivalents
- Support both named outputs (`emit: fastqc_out`) and positional outputs
- Return list of dicts matching the input format expected by `execute()`

#### 1.2 Add `get_named_outputs()` method
```python
def get_named_outputs(self):
    """
    Get outputs as a dictionary keyed by channel name.

    Returns:
        Dict mapping output channel names to their values

    Example:
        outputs = result.get_named_outputs()
        print(outputs['trimmed_reads'])  # Access specific output
    """
```

**Implementation details**:
- Parse output channel names from `WorkflowOutputEvent.getName()`
- Group outputs by name
- Handle unnamed outputs (use indices like "output_0", "output_1")

#### 1.3 Add `get_output_paths()` method
```python
def get_output_paths(self, pattern=None):
    """
    Get only file paths from outputs, optionally filtered by pattern.

    Args:
        pattern: Optional glob pattern to filter files (e.g., "*.fastq")

    Returns:
        List of Path objects
    """
```

#### 1.4 Add `to_dict()` method for inspection
```python
def to_dict(self):
    """
    Convert all result data to a plain Python dict for inspection.

    Useful for debugging and understanding module outputs.
    """
```

### Phase 2: Update NextflowEngine Input Handling (src/pynf/engine.py)

**Goal**: Make `execute()` accept NextflowResult objects directly.

#### 2.1 Enhance `execute()` signature
```python
def execute(self, script_path, executor="local", params=None,
            inputs=None, config=None, docker_config=None, verbose=False):
    """
    Execute a Nextflow script with optional Docker configuration.

    Args:
        inputs: List of dicts OR NextflowResult from previous execution.
                When NextflowResult is passed, automatically converts to input format.
    """
    # Add auto-conversion logic
    if isinstance(inputs, NextflowResult):
        inputs = inputs.to_inputs()
```

#### 2.2 Improve output-to-input data conversion

Current `_convert_to_java_type()` needs enhancements:
- Better handling of file paths (preserve Path objects vs strings)
- Support for nested structures (lists of tuples, etc.)
- Meta map validation and conversion
- Handle output channel objects from previous runs

### Phase 3: Create Chaining Utilities (src/pynf/chaining.py - NEW FILE)

**Goal**: Provide convenience functions for common chaining patterns.

#### 3.1 `chain()` function
```python
def chain(*steps, verbose=False, return_all=False):
    """
    Execute a sequence of Nextflow modules, passing outputs to next inputs.

    Args:
        *steps: Tuples of (script_path, additional_inputs_dict)
        verbose: Enable verbose output for all steps
        return_all: Return list of all results (default: only last result)

    Returns:
        NextflowResult (or list if return_all=True)

    Example:
        result = chain(
            ("modules/fastqc.nf", [{"reads": "sample.fastq"}]),
            ("modules/trimming.nf", {}),
            ("modules/alignment.nf", {"reference": "ref.fa"})
        )
    """
```

**Implementation**:
- Loop through steps
- For first step, use provided inputs
- For subsequent steps, merge previous outputs with additional inputs
- Handle input conflicts (error if same key in both outputs and additional inputs)
- Track all intermediate results if requested

#### 3.2 `parallel()` function
```python
def parallel(script_paths, inputs, **kwargs):
    """
    Run multiple modules in parallel on the same inputs.

    Useful for running different QC tools on same data.

    Args:
        script_paths: List of script paths
        inputs: Input data (list of dicts or NextflowResult)
        **kwargs: Additional execute() parameters

    Returns:
        Dict mapping script_path to NextflowResult
    """
```

**Implementation**:
- Use Python threading/multiprocessing to launch multiple executions
- Each gets its own JVM session (JVM is already running, sessions are lightweight)
- Collect and return all results

#### 3.3 Output transformation utilities
```python
def filter_outputs(result, predicate):
    """Filter outputs based on a predicate function."""

def map_outputs(result, transform):
    """Transform outputs using a mapping function."""

def merge_results(*results):
    """Merge outputs from multiple results."""
```

### Phase 4: Testing & Examples

#### 4.1 Create test Nextflow scripts

**nextflow_scripts/module-a.nf** (Producer):
```nextflow
process produceData {
    output:
    path "data.txt"

    script:
    """
    echo "Sample data" > data.txt
    """
}

workflow {
    produceData()
    emit: produceData.out
}
```

**nextflow_scripts/module-b.nf** (Consumer):
```nextflow
process consumeData {
    input:
    path input_file

    output:
    path "processed.txt"

    script:
    """
    cat ${input_file} | tr '[:lower:]' '[:upper:]' > processed.txt
    """
}

workflow {
    consumeData(Channel.fromPath(params.input_file))
    emit: consumeData.out
}
```

**nextflow_scripts/module-c.nf** (Mixed inputs):
```nextflow
process merge {
    input:
    path data_file
    val reference

    output:
    path "merged.txt"

    script:
    """
    echo "Data: \$(cat ${data_file})" > merged.txt
    echo "Reference: ${reference}" >> merged.txt
    """
}
```

#### 4.2 Create test cases (tests/test_chaining.py)

```python
def test_basic_chaining():
    """Test basic two-module chain."""
    result1 = run_module("nextflow_scripts/module-a.nf")
    result2 = run_module("nextflow_scripts/module-b.nf",
                        inputs=result1.to_inputs())

    outputs = result2.get_output_files()
    assert any("processed.txt" in str(p) for p in outputs)

def test_chain_convenience_function():
    """Test chain() helper."""
    from pynf.chaining import chain

    result = chain(
        ("nextflow_scripts/module-a.nf", None),
        ("nextflow_scripts/module-b.nf", None)
    )

    assert result.get_output_files()

def test_chain_with_mixed_inputs():
    """Test chaining with additional parameters."""
    result1 = run_module("nextflow_scripts/module-a.nf")
    result2 = run_module("nextflow_scripts/module-c.nf",
                        inputs=result1.to_inputs(),
                        params={"reference": "hg38"})

    # Verify both inputs were used
    outputs = result2.get_output_files()
    assert outputs

def test_named_outputs():
    """Test extracting named outputs."""
    result = run_module("nextflow_scripts/module-a.nf")
    named = result.get_named_outputs()

    assert isinstance(named, dict)
    assert len(named) > 0

def test_parallel_execution():
    """Test running multiple modules on same input."""
    from pynf.chaining import parallel

    results = parallel(
        ["nextflow_scripts/module-a.nf", "nextflow_scripts/module-b.nf"],
        inputs=[{"data": "test.txt"}]
    )

    assert len(results) == 2
```

#### 4.3 Update README with chaining examples

Add a new section "Chaining Modules" with:
- Basic example
- Complex pipeline example
- Parallel execution example
- Best practices

### Phase 5: Documentation & Polish

#### 5.1 Add docstrings
- Comprehensive docstrings for all new methods
- Include examples in docstrings

#### 5.2 Type hints
```python
from typing import List, Dict, Optional, Union, Any
from pathlib import Path

def to_inputs(self, channel_mapping: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
    ...
```

#### 5.3 Error handling
- Clear error messages when output format doesn't match input expectations
- Validation of channel mappings
- Handle missing outputs gracefully

## Technical Challenges & Solutions

### Challenge 1: Output Format Mismatch
**Problem**: Module A outputs `path "file.txt"` but Module B expects `tuple val(meta), path(reads)`

**Solution**:
- Support flexible `channel_mapping` in `to_inputs()`
- Add validation warnings when structure mismatch detected
- Document common patterns and transformations

### Challenge 2: Java Object Conversion
**Problem**: Outputs from Nextflow are Java objects (HashMap, ArrayList, Path)

**Solution**:
- Extend `_flatten_paths()` logic in result.py
- Comprehensive type conversion in `to_inputs()`
- Handle all Java collection types properly

### Challenge 3: Session Management
**Problem**: Each module needs fresh session but JVM is already running

**Solution**:
- Current approach already handles this correctly
- Each `engine.execute()` creates new `Session` object
- JVM remains running but sessions are independent
- No changes needed - architecture already supports this

### Challenge 4: Meta Maps
**Problem**: nf-core modules heavily use meta maps `[meta: [id: 'sample1'], reads: [...]]`

**Solution**:
- Preserve meta maps through chain
- Add helpers to create/modify meta maps
- Validate meta map structure before passing to module

## Nextflow JVM Classes Used

### Already Used:
- `nextflow.Session` - execution context
- `nextflow.script.ScriptLoaderFactory` - parse scripts
- `nextflow.trace.TraceObserverV2` - capture events
- `WorkflowOutputEvent` - workflow output signals
- `FilePublishEvent` - file publication signals

### Will Use for Chaining:
- `groovyx.gpars.dataflow.DataflowChannel` - channel objects
- `nextflow.script.ChannelOut` - process/workflow outputs
- `java.util.HashMap` - for meta maps
- `java.nio.file.Path` - file path handling
- Output parameter classes from `nextflow.script.params.v2.*`

## Success Criteria

Implementation is complete when:

1. ✓ Can chain two modules with file outputs/inputs
2. ✓ Can chain modules with mixed inputs (outputs + params)
3. ✓ Can extract and inspect named outputs
4. ✓ `chain()` convenience function works for 3+ modules
5. ✓ All tests pass
6. ✓ README updated with clear examples
7. ✓ Works in Jupyter notebooks
