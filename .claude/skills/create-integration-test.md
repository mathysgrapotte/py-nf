# create-integration-test

## Description

Generate pytest integration tests for Nextflow modules following py-nf project patterns. This skill scaffolds properly structured test functions that validate module execution, output files, and workflow outputs.

## When to Use

Use this skill when you need to:

- **Add test coverage** for a new Nextflow module
- **Convert** manual testing into automated pytest tests
- **Formalize** validation after prototyping a module
- **Ensure** regression testing for existing modules
- **Follow** project testing conventions consistently

## Keywords

pytest, integration testing, test generation, nextflow module testing, test scaffold, automation

## Instructions

When the user requests to create an integration test, follow these steps:

### 1. Gather Requirements

Ask the user for:

- **Script path**: Which `.nf` file to test
- **Test name**: Descriptive test function name (suggest based on script)
- **Expected outputs**: What files/values should the module produce
- **Input parameters**: Any params or input files needed
- **Validation criteria**: Success conditions (file exists, content matches, etc.)

### 2. Analyze the Script

Read the target `.nf` script to understand:

- Process names and outputs
- Published files or emit declarations
- Required parameters
- Expected execution behavior

```python
# Example analysis
script = read_file("nextflow_scripts/my-process.nf")
# Look for:
# - process definitions
# - output: path(...) declarations
# - publishDir directives
# - emit: statements in workflows
```

### 3. Generate Test Function

Follow the existing pattern from `tests/test_integration.py`:

```python
def test_<descriptive_name>():
    """Brief description of what this test validates"""

    # Setup
    engine = NextflowEngine()
    script_path = engine.load_script("path/to/script.nf")

    # Optional: Set up params or inputs
    params = {"param_name": "value"}  # If needed
    input_files = ["data/input.txt"]  # If needed

    # Execute
    result = engine.execute(
        script_path,
        params=params,  # Optional
        input_files=input_files  # Optional
    )

    # Validate outputs
    outputs = result.get_output_files()

    # Assertion 1: Check specific file exists
    assert any(Path(path).name == "expected_output.txt" for path in outputs), \
        f"Expected expected_output.txt in {[Path(p).name for p in outputs]}"

    # Assertion 2: Check file content (if needed)
    output_path = next(p for p in outputs if Path(p).name == "expected_output.txt")
    content = Path(output_path).read_text()
    assert "expected content" in content, f"Unexpected content: {content}"

    # Assertion 3: Check execution report (if needed)
    report = result.get_execution_report()
    assert report["completed_tasks"] > 0, "No tasks completed"
    assert report["failed_tasks"] == 0, "Some tasks failed"

    # Assertion 4: Check workflow outputs (if module has emit)
    workflow_outputs = result.get_workflow_outputs()
    assert len(workflow_outputs) > 0, "No workflow outputs found"
    assert workflow_outputs[0]["name"] == "expected_name"

    print(f"✓ {test_name} passed")
```

### 4. Add to Test File

Determine where to add the test:

- **Existing file**: Append to `tests/test_integration.py`
- **New file**: Create new test file if testing different subsystem
- **Group tests**: Keep related tests together

### 5. Follow Project Patterns

Ensure the test follows py-nf conventions:

**Import pattern:**

```python
from pathlib import Path
from pynf import NextflowEngine, run_module
```

**Test structure:**

```python
def test_<module>_<behavior>():
    """Test that <module> <behavior> correctly"""
    # Arrange
    engine = NextflowEngine()
    script_path = engine.load_script("...")

    # Act
    result = engine.execute(script_path)

    # Assert
    outputs = result.get_output_files()
    assert condition, "failure message"
```

**Assertion patterns:**

```python
# File existence
assert any(Path(p).name == "file.txt" for p in outputs), outputs

# Multiple files
expected_files = ["output1.txt", "output2.txt"]
output_names = [Path(p).name for p in outputs]
for expected in expected_files:
    assert expected in output_names, f"Missing {expected}"

# File content
output_path = next(p for p in outputs if Path(p).name == "target.txt")
assert Path(output_path).read_text().strip() == "expected"

# Execution success
report = result.get_execution_report()
assert report["failed_tasks"] == 0
```

### 6. Run and Verify

Execute the new test:

```bash
# Run specific test
uv run pytest tests/test_integration.py::test_<name> -v

# Run all integration tests
uv run pytest tests/test_integration.py -v
```

### 7. Document the Test

Add docstring explaining:

- What module is being tested
- What behavior is validated
- Any special setup or assumptions
- Expected outputs

Example:

```python
def test_samtools_index_produces_bai():
    """
    Test that samtools index process produces .bai index file.

    This test validates:
    - Process executes successfully with BAM input
    - Output .bai file is created
    - Index file is published to expected location
    """
```

## Example Workflows

### Example 1: Simple Output File Test

**User:** "Create a test for the hello-world.nf script"

**Steps:**

1. Read `nextflow_scripts/hello-world.nf`
2. Identify it prints to stdout
3. Generate test:

```python
def test_hello_world_prints_greeting():
    """Test that hello-world process prints greeting"""
    engine = NextflowEngine()
    script_path = engine.load_script("nextflow_scripts/hello-world.nf")
    result = engine.execute(script_path)

    stdout = result.get_stdout()
    assert "Hello" in stdout, f"Expected greeting, got: {stdout}"

    print("✓ hello-world test passed")
```

### Example 2: File Output with Parameters

**User:** "Test the file-output-process with custom output name"

```python
def test_file_output_with_custom_name():
    """Test file-output-process accepts output_name parameter"""
    engine = NextflowEngine()
    script_path = engine.load_script("nextflow_scripts/file-output-process.nf")

    result = engine.execute(
        script_path,
        params={"output_name": "custom.txt"}
    )

    outputs = result.get_output_files()
    assert any(Path(p).name == "custom.txt" for p in outputs), \
        f"Expected custom.txt, got: {[Path(p).name for p in outputs]}"

    # Verify content
    custom_file = next(p for p in outputs if Path(p).name == "custom.txt")
    assert Path(custom_file).exists()
    assert Path(custom_file).stat().st_size > 0

    print("✓ custom output name test passed")
```

### Example 3: Multiple Output Validation

**User:** "Test a process that produces multiple output files"

```python
def test_multi_output_process():
    """Test process that produces index, stats, and log files"""
    engine = NextflowEngine()
    script_path = engine.load_script("nextflow_scripts/multi-output.nf")

    result = engine.execute(script_path)

    outputs = result.get_output_files()
    output_names = [Path(p).name for p in outputs]

    # Validate all expected outputs present
    expected = ["output.bam", "output.bam.bai", "stats.txt", "process.log"]
    for expected_file in expected:
        assert expected_file in output_names, \
            f"Missing {expected_file}. Found: {output_names}"

    # Validate file sizes
    for path in outputs:
        assert Path(path).stat().st_size > 0, f"Empty file: {path}"

    print("✓ multi-output test passed")
```

## Common Test Patterns

### Testing Workflow Outputs (emit:)

```python
def test_workflow_emit_outputs():
    """Test workflow emit declarations are captured"""
    result = engine.execute(script_path)

    workflow_outputs = result.get_workflow_outputs()
    assert len(workflow_outputs) > 0, "No workflow outputs"

    # Check specific emit name
    output_names = [o["name"] for o in workflow_outputs]
    assert "results" in output_names
```

### Testing with Input Files

```python
def test_process_with_inputs():
    """Test process handles input files correctly"""
    result = engine.execute(
        script_path,
        input_files=["data/sample1.fastq", "data/sample2.fastq"]
    )

    outputs = result.get_output_files()
    # Validate outputs correspond to inputs
    assert len(outputs) == 2
```

### Testing Error Conditions

```python
def test_process_fails_gracefully_with_invalid_input():
    """Test process error handling"""
    with pytest.raises(Exception) as exc_info:
        result = engine.execute(
            script_path,
            params={"required_param": None}  # Invalid
        )
    assert "required" in str(exc_info.value).lower()
```

## Tips for Effective Tests

1. **Descriptive names**: Use `test_<module>_<behavior>_<condition>` format
2. **Clear assertions**: Include helpful failure messages
3. **Minimal setup**: Only include necessary params/inputs
4. **Fast execution**: Prefer small test datasets
5. **Independence**: Each test should run standalone
6. **Documentation**: Explain non-obvious validation logic

## Integration with Development Workflow

**Development cycle:**

1. Write `.nf` module
2. Use `test-nextflow-module` skill to validate manually
3. Use this skill to create formal pytest test
4. Run test suite: `uv run pytest tests/`
5. Commit with jj: `jj commit -m "Add tests for module"`

## Related Skills

- **test-nextflow-module**: Quick manual testing before creating pytest
- **debug-observer-events**: Fix output collection issues in tests
- **setup-nextflow-env**: Ensure test environment is configured
