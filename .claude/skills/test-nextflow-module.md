# test-nextflow-module

## Description

Run a Nextflow `.nf` script through py-nf's engine and validate its outputs. This skill provides a quick way to test Nextflow modules during development without writing formal pytest tests.

## When to Use

Use this skill when you need to:

- **Quickly validate** a Nextflow script works with py-nf
- **Inspect outputs** from a module or workflow
- **Debug** execution issues before writing formal tests
- **Verify** file outputs and execution reports
- **Prototype** new Nextflow scripts

## Keywords

nextflow testing, module execution, output validation, quick test, debugging, .nf scripts

## Instructions

When the user requests to test a Nextflow module, follow these steps:

### 1. Identify the Script

Ask the user which `.nf` file to test if not specified. Common locations:

- `nextflow_scripts/*.nf` - Test scripts
- `*.nf` - Root level scripts
- `nextflow/tests/*.nf` - Nextflow's own test scripts

### 2. Create Test Script

Create a temporary Python script that uses py-nf to execute the module:

```python
#!/usr/bin/env python3
"""Quick test of Nextflow module"""

from pathlib import Path
from pynf import NextflowEngine

def test_module(script_path: str, params=None, input_files=None):
    """Execute a Nextflow script and report results"""

    print(f"Testing: {script_path}")
    print("=" * 70)

    # Create engine
    engine = NextflowEngine()

    # Load script
    script = engine.load_script(script_path)
    print(f"Loaded script: {script}")

    # Execute with optional params and inputs
    print("\nExecuting...")
    result = engine.execute(
        script,
        params=params,
        input_files=input_files
    )

    # Report results
    print("\n" + "=" * 70)
    print("EXECUTION REPORT")
    print("=" * 70)
    report = result.get_execution_report()
    for key, value in report.items():
        print(f"  {key}: {value}")

    print("\n" + "=" * 70)
    print("OUTPUT FILES")
    print("=" * 70)
    output_files = result.get_output_files()
    if output_files:
        for path in output_files:
            p = Path(path)
            print(f"  - {p.name} ({p})")
            if p.exists():
                print(f"    Size: {p.stat().st_size} bytes")
    else:
        print("  (no output files)")

    print("\n" + "=" * 70)
    print("WORKFLOW OUTPUTS")
    print("=" * 70)
    workflow_outputs = result.get_workflow_outputs()
    if workflow_outputs:
        for output in workflow_outputs:
            print(f"  - {output['name']}: {output['value']}")
    else:
        print("  (no workflow outputs)")

    print("\n" + "=" * 70)
    print("STDOUT")
    print("=" * 70)
    stdout = result.get_stdout()
    if stdout:
        print(stdout)
    else:
        print("  (no stdout)")

    return result

if __name__ == "__main__":
    # Test the module
    result = test_module(
        "SCRIPT_PATH_HERE",
        params=None,  # Add params dict if needed
        input_files=None  # Add input files list if needed
    )

    print("\n✓ Test completed successfully")
```

### 3. Run the Test

Execute the test script:

```bash
uv run python test_module_temp.py
```

### 4. Analyze Results

Check the output for:

- **Execution report**: Task counts, work directory
- **Output files**: Verify expected files exist and have content
- **Workflow outputs**: Check emit values from workflow blocks
- **Stdout**: Review process output
- **Errors**: Look for Java exceptions or Nextflow errors

### 5. Common Issues

**JAR not found:**

```
FileNotFoundError: Nextflow JAR not found
```

Solution: Run `python setup_nextflow.py`

**No output files:**

- Check if observer captured events (DEBUG output)
- Verify workdir exists and has files
- Ensure process has `output:` declarations or `publishDir`

**Java exceptions:**

- Check .nf script syntax
- Verify Nextflow version compatibility
- Review params match script expectations

**Empty stdout:**

- Process may not have stdout output
- Check `.command.out` in work directory manually

### 6. Optional Enhancements

For more complex testing needs:

**With parameters:**

```python
result = test_module(
    "script.nf",
    params={"threads": 4, "output_name": "results.txt"}
)
```

**With input files:**

```python
result = test_module(
    "script.nf",
    input_files=["data/sample1.txt", "data/sample2.txt"]
)
```

**Validate specific outputs:**

```python
output_files = result.get_output_files()
assert any(Path(p).name == "output.txt" for p in output_files), \
    f"Expected output.txt, got: {[Path(p).name for p in output_files]}"
```

### 7. Clean Up

After testing, optionally clean up work directories:

```bash
rm -rf work/ .nextflow/ .nextflow.log*
```

## Example Usage

**User:** "Test the file-output-process.nf script"

**Assistant Response:**

```
I'll create a quick test for file-output-process.nf and run it.

[Creates and runs test script]

Results:
- Execution completed: 1 task succeeded
- Output files: output.txt (28 bytes)
- Work directory: work/abc123...
- Process "writeFile" produced expected output

✓ Test passed - module works correctly
```

## Integration with Development Workflow

This skill complements the project workflow:

- **Before pytest**: Quick validation before writing formal tests
- **During debugging**: Inspect outputs when tests fail
- **After changes**: Verify modifications work
- **For documentation**: Generate example outputs

## Related Skills

- **create-integration-test**: Convert successful manual test to pytest
- **debug-observer-events**: Investigate output collection issues
- **setup-nextflow-env**: Fix environment if JAR not found
