# debug-observer-events

## Description

Diagnose and troubleshoot TraceObserverV2 event collection issues in py-nf. This skill helps identify why output files aren't being captured by the observer, whether events are firing correctly, and if the fallback workdir scanning is functioning.

## When to Use

Use this skill when:

- **Output files are missing** from `result.get_output_files()`
- **Observer events aren't firing** (empty workflow_events or file_events)
- **Fallback scanning fails** to find files in work directories
- **Debugging path flattening** logic for complex Java types
- **Investigating** observer registration issues
- **Comparing** observer-based vs workdir-based collection

## Keywords

debugging, TraceObserverV2, output collection, events, observer, troubleshooting, missing outputs

## Instructions

When the user reports output collection issues or wants to debug the observer, follow this systematic approach:

### 1. Identify the Problem

Ask the user:

- Which `.nf` script is failing?
- What outputs are expected but missing?
- Are they seeing the DEBUG output messages?
- Does the script work in standard `nextflow run`?

### 2. Enable Verbose Debugging

The observer already has DEBUG prints, but we can enhance them temporarily:

**Modify `src/pynf/engine.py`** to add more detailed logging:

```python
# In _WorkflowOutputCollector class

def onWorkflowOutput(self, event):
    print(f"DEBUG: onWorkflowOutput fired!")
    print(f"  - name: {event.getName()}")
    print(f"  - value type: {type(event.getValue())}")
    print(f"  - value: {event.getValue()}")
    print(f"  - index: {event.getIndex()}")
    self._workflow_events.append({
        "name": event.getName(),
        "value": event.getValue(),
        "index": event.getIndex(),
    })

def onFilePublish(self, event):
    print(f"DEBUG: onFilePublish fired!")
    print(f"  - target: {event.getTarget()}")
    print(f"  - source: {event.getSource()}")
    print(f"  - labels: {event.getLabels()}")
    self._file_events.append({
        "target": event.getTarget(),
        "source": event.getSource(),
        "labels": event.getLabels(),
    })
```

### 3. Verify Observer Registration

Check if observer is properly attached to session:

```python
# In NextflowEngine.execute(), after observer registration:

print(f"DEBUG: Observer registered: {observer_registered}")
if observer_registered:
    print(f"DEBUG: Session observersV2 count: {len(session.getObserversV2())}")
    print(f"DEBUG: Observer proxy type: {type(observer_proxy)}")
else:
    print("WARNING: Observer registration failed - will rely on workdir fallback")
```

### 4. Inspect Event Collection

Add diagnostic output after execution:

```python
# After session.await_() completes:

print(f"\n{'=' * 70}")
print("OBSERVER EVENT DIAGNOSTICS")
print('=' * 70)
print(f"Workflow events collected: {len(collector.workflow_events())}")
for i, event in enumerate(collector.workflow_events()):
    print(f"  [{i}] {event}")

print(f"\nFile events collected: {len(collector.file_events())}")
for i, event in enumerate(collector.file_events()):
    print(f"  [{i}] {event}")

print(f"\nTask workdirs tracked: {len(collector.task_workdirs())}")
for i, workdir in enumerate(collector.task_workdirs()):
    print(f"  [{i}] {workdir}")
    # Verify workdir exists
    from pathlib import Path
    p = Path(workdir)
    if p.exists():
        files = list(p.iterdir())
        print(f"      Files: {[f.name for f in files]}")
    else:
        print(f"      WARNING: Workdir does not exist!")
```

### 5. Test Path Flattening

If events are firing but paths aren't extracted, test the flattening logic:

```python
# Create a test script to isolate path flattening:

from pynf.result import NextflowResult

def test_flatten_paths(test_value):
    """Test if a value can be flattened to paths"""
    result = NextflowResult(None, None, None)

    print(f"Testing value: {test_value}")
    print(f"Value type: {type(test_value)}")

    paths = list(result._flatten_paths(test_value))

    print(f"Extracted paths: {len(paths)}")
    for path in paths:
        print(f"  - {path}")

    return paths

# Test with actual event values
import jpype
# ... start JVM and get actual event value ...
paths = test_flatten_paths(event.getValue())
```

### 6. Compare Observer vs Fallback

Temporarily disable observer collection to test fallback:

```python
# In NextflowEngine.execute()
# Comment out observer registration:

# collector = _WorkflowOutputCollector()
# observer_proxy = jpype.JProxy(self.TraceObserverV2, inst=collector)
# observer_registered = self._register_output_observer(session, observer_proxy)

# Force fallback
result = NextflowResult(
    script,
    session,
    loader,
    workflow_events=[],  # Empty - force fallback
    file_events=[],
    task_workdirs=[]  # Will scan session.getWorkDir()
)
```

Then check if fallback finds the files:

```bash
uv run python test_script.py
# Look for "Workdir scan paths:" in output
```

### 7. Inspect Java Event Objects

If events fire but have unexpected structure:

```python
# Add this to observer methods:

def onFilePublish(self, event):
    print(f"\n{'=' * 50}")
    print("Java Event Object Inspection")
    print('=' * 50)

    # Introspect the event object
    print(f"Event class: {event.getClass()}")

    # List all methods
    methods = event.getClass().getMethods()
    print(f"Available methods: {len(methods)}")
    for method in methods[:10]:  # First 10
        print(f"  - {method.getName()}")

    # Try different accessor patterns
    try:
        target = event.getTarget()
        print(f"getTarget() = {target} (type: {type(target)})")
    except Exception as e:
        print(f"getTarget() failed: {e}")

    try:
        source = event.getSource()
        print(f"getSource() = {source} (type: {type(source)})")
    except Exception as e:
        print(f"getSource() failed: {e}")
```

### 8. Check Nextflow Version Compatibility

Verify TraceObserverV2 is available:

```python
# Add version check:

import jpype

if not jpype.isJVMStarted():
    jpype.startJVM(classpath=[nextflow_jar_path])

try:
    TraceObserverV2 = jpype.JClass("nextflow.trace.TraceObserverV2")
    print(f"✓ TraceObserverV2 available: {TraceObserverV2}")
except Exception as e:
    print(f"✗ TraceObserverV2 not available: {e}")
    print("This Nextflow version may not support TraceObserverV2")
    print("Upgrade Nextflow to 23.10+ for observer support")
```

### 9. Manual Workdir Inspection

If all else fails, manually verify work directories:

```bash
# After running test:
ls -la work/
# Find task directories
find work -name ".command.out" -o -name ".command.log"
# Check for output files
find work -type f ! -name ".*"
```

Then check if those files match what the script should produce.

## Common Issues and Solutions

### Issue 1: Observer Events Never Fire

**Symptoms:**

- No DEBUG output from `onWorkflowOutput` or `onFilePublish`
- All event lists are empty
- Fallback scanning triggers

**Diagnosis:**

```python
# Check if observer is registered
print(f"Observer registered: {observer_registered}")

# Check if script has publish directives
with open(script_path) as f:
    content = f.read()
    has_publish = "publishDir" in content
    has_emit = "emit:" in content
    print(f"Script has publishDir: {has_publish}")
    print(f"Script has emit: {has_emit}")
```

**Solutions:**

- Ensure Nextflow version >= 23.10
- Check if script actually publishes files or emits outputs
- Verify observer registration succeeded
- Try raw module (process only) vs workflow

### Issue 2: Events Fire but No Paths Extracted

**Symptoms:**

- `onFilePublish` prints show events
- But `result.get_output_files()` returns empty list
- Flattening logic fails to extract paths

**Diagnosis:**

```python
# In onFilePublish:
target = event.getTarget()
print(f"Target type: {type(target)}")
print(f"Target value: {target}")

# Test flattening specifically:
from pynf.result import NextflowResult
dummy = NextflowResult(None, None, None)
paths = list(dummy._flatten_paths(target))
print(f"Flattened to: {paths}")
```

**Solutions:**

- Add handling for new Java type in `_flatten_paths()`
- Check if target is wrapped in unexpected collection
- Verify paths are absolute (use `.toAbsolutePath()`)

### Issue 3: Workdir Fallback Finds Nothing

**Symptoms:**

- Observer collection fails (expected)
- Fallback scan also returns empty
- But files exist in work directory

**Diagnosis:**

```python
# Check tracked workdirs:
for workdir in collector.task_workdirs():
    p = Path(workdir)
    print(f"Workdir: {workdir}")
    print(f"  Exists: {p.exists()}")
    if p.exists():
        all_files = list(p.iterdir())
        print(f"  All files: {[f.name for f in all_files]}")
        non_hidden = [f for f in all_files if not f.name.startswith('.')]
        print(f"  Non-hidden: {[f.name for f in non_hidden]}")
```

**Solutions:**

- Check if `onTaskComplete` is firing
- Verify workdir paths are correct
- Ensure files aren't hidden (start with `.`)
- Check file permissions

### Issue 4: Wrong Files Collected

**Symptoms:**

- Files are found but wrong ones (e.g., `.command.*` files)
- Or files from old runs

**Diagnosis:**

```python
# Check if work directory was cleaned:
import os
print(f"Work dir modified: {os.path.getmtime('work')}")

# List all files found:
for path in result.get_output_files():
    p = Path(path)
    print(f"{p.name} - modified {os.path.getmtime(path)}")
```

**Solutions:**

- Clean work directory before test: `rm -rf work/ .nextflow/`
- Filter out `.command.*` files explicitly
- Use observer collection (more precise than workdir scan)

## Debugging Workflow

**Step-by-step debugging process:**

1. **Confirm the problem**: Run test and check output
2. **Enable verbose logging**: Add DEBUG prints to observer
3. **Check observer registration**: Verify it attached to session
4. **Monitor event firing**: Watch for `onFilePublish` / `onWorkflowOutput`
5. **Inspect event objects**: Print types and values
6. **Test path flattening**: Isolate flattening logic
7. **Verify workdirs**: Check fallback scan finds files
8. **Compare with nextflow CLI**: Run `nextflow run script.nf` directly
9. **Check Nextflow version**: Ensure TraceObserverV2 support
10. **Isolate the issue**: Determine if engine, observer, or result problem

## Example Debugging Session

```python
#!/usr/bin/env python3
"""Debug observer event collection"""

from pynf import NextflowEngine
from pathlib import Path

def debug_observer():
    print("Starting observer debug session...")

    engine = NextflowEngine()
    script_path = engine.load_script("nextflow_scripts/problematic.nf")

    print(f"\n{'=' * 70}")
    print("EXECUTING SCRIPT")
    print('=' * 70)

    result = engine.execute(script_path)

    print(f"\n{'=' * 70}")
    print("RESULTS")
    print('=' * 70)

    # Check what we got
    outputs = result.get_output_files()
    print(f"Output files found: {len(outputs)}")
    for output in outputs:
        print(f"  - {Path(output).name}: {output}")

    workflow_outputs = result.get_workflow_outputs()
    print(f"\nWorkflow outputs: {len(workflow_outputs)}")
    for wo in workflow_outputs:
        print(f"  - {wo}")

    # Check report
    report = result.get_execution_report()
    print(f"\nExecution report:")
    print(f"  Completed: {report['completed_tasks']}")
    print(f"  Failed: {report['failed_tasks']}")
    print(f"  Work dir: {report['work_dir']}")

    # Manually check work directory
    print(f"\n{'=' * 70}")
    print("MANUAL WORK DIRECTORY CHECK")
    print('=' * 70)

    work_dir = Path(report['work_dir'])
    if work_dir.exists():
        for hash_prefix in work_dir.iterdir():
            if hash_prefix.is_dir():
                for task_dir in hash_prefix.iterdir():
                    if task_dir.is_dir():
                        print(f"\nTask dir: {task_dir}")
                        files = list(task_dir.iterdir())
                        for f in files:
                            size = f.stat().st_size if f.is_file() else "dir"
                            print(f"  - {f.name} ({size} bytes)")

if __name__ == "__main__":
    debug_observer()
```

## Integration with Development Workflow

Use this skill when:

- Test failures show missing outputs
- Developing new path extraction logic
- Supporting new Nextflow output patterns
- Troubleshooting user-reported issues
- Validating observer improvements

## Related Skills

- **test-nextflow-module**: Run scripts to trigger observer
- **analyze-java-types**: Inspect complex Java event objects
- **create-integration-test**: Add tests after fixing observer issues
