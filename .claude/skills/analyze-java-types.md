# analyze-java-types

## Description

Inspect and analyze Java object types returned from Nextflow classes through JPype. This skill helps developers understand complex nested Java structures, explore available methods and fields, and implement proper handling code for the `_flatten_paths()` method and other Java interop scenarios.

## When to Use

Use this skill when:

- **Implementing** new output collection strategies
- **Debugging** path extraction from Java objects
- **Exploring** unfamiliar Nextflow classes
- **Understanding** event object structures
- **Adding support** for new Java types in `_flatten_paths()`
- **Troubleshooting** JPype type conversion issues
- **Documenting** Java API surface area

## Keywords

java introspection, jpype, type analysis, java objects, reflection, nextflow classes, debugging

## Instructions

When the user needs to understand Java types or implement handling for them, follow this approach:

### 1. Capture the Java Object

First, obtain the Java object you want to analyze. Common sources:

**From Observer Events:**

```python
# In _WorkflowOutputCollector
def onFilePublish(self, event):
    target = event.getTarget()
    # Save for analysis
    import pickle
    with open('/tmp/event_target.pkl', 'wb') as f:
        pickle.dump(target, f)
```

**From Execution Results:**

```python
result = engine.execute(script_path)
workflow_outputs = result.get_workflow_outputs()
value = workflow_outputs[0]['value']  # The Java object
```

**From Session/Script Objects:**

```python
session = result.session
workdir = session.getWorkDir()  # Returns java.nio.file.Path
```

### 2. Create Analysis Script

Generate a comprehensive type inspector:

```python
#!/usr/bin/env python3
"""Analyze Java object types and structure"""

import jpype
import jpype.imports
from pathlib import Path


def analyze_java_object(obj, depth=0, max_depth=3):
    """
    Recursively analyze a Java object's type, methods, fields, and structure.

    Args:
        obj: The Java object to analyze
        depth: Current recursion depth (internal)
        max_depth: Maximum recursion depth to prevent infinite loops
    """
    indent = "  " * depth

    if depth > max_depth:
        print(f"{indent}[Max depth reached]")
        return

    print(f"{indent}{'=' * (60 - depth * 2)}")
    print(f"{indent}OBJECT ANALYSIS (depth={depth})")
    print(f"{indent}{'=' * (60 - depth * 2)}")

    # Basic type information
    print(f"{indent}Python type: {type(obj)}")
    print(f"{indent}Python repr: {repr(obj)[:100]}")

    # Check if it's a Java object
    if not hasattr(obj, 'getClass'):
        print(f"{indent}→ Not a Java object (Python native type)")
        return

    # Java class information
    try:
        java_class = obj.getClass()
        print(f"{indent}Java class: {java_class.getName()}")
        print(f"{indent}Simple name: {java_class.getSimpleName()}")

        # Superclass
        superclass = java_class.getSuperclass()
        if superclass:
            print(f"{indent}Superclass: {superclass.getName()}")

        # Interfaces
        interfaces = java_class.getInterfaces()
        if len(interfaces) > 0:
            print(f"{indent}Interfaces: {[i.getName() for i in interfaces]}")

    except Exception as e:
        print(f"{indent}Error getting class info: {e}")

    # Methods
    print(f"\n{indent}METHODS:")
    try:
        methods = obj.getClass().getMethods()
        # Group methods by name
        method_names = set()
        for method in methods:
            method_name = method.getName()
            if not method_name.startswith('_') and method_name not in method_names:
                method_names.add(method_name)

        # Show important methods first
        important = ['get', 'size', 'iterator', 'next', 'hasNext', 'toString',
                     'toAbsolutePath', 'toPath', 'getName', 'getValue', 'getKey']

        priority_methods = [m for m in sorted(method_names) if any(imp in m for imp in important)]
        other_methods = [m for m in sorted(method_names) if m not in priority_methods]

        print(f"{indent}  Important methods ({len(priority_methods)}):")
        for method_name in priority_methods[:10]:  # First 10
            print(f"{indent}    - {method_name}()")

        if other_methods:
            print(f"{indent}  Other methods ({len(other_methods)}):")
            for method_name in other_methods[:5]:  # First 5
                print(f"{indent}    - {method_name}()")
            if len(other_methods) > 5:
                print(f"{indent}    ... and {len(other_methods) - 5} more")

    except Exception as e:
        print(f"{indent}  Error listing methods: {e}")

    # Fields
    print(f"\n{indent}FIELDS:")
    try:
        fields = obj.getClass().getDeclaredFields()
        for field in fields[:10]:  # First 10 fields
            field.setAccessible(True)
            field_name = field.getName()
            try:
                field_value = field.get(obj)
                print(f"{indent}  - {field_name}: {type(field_value).__name__}")
            except:
                print(f"{indent}  - {field_name}: [inaccessible]")
        if len(fields) > 10:
            print(f"{indent}  ... and {len(fields) - 10} more fields")
    except Exception as e:
        print(f"{indent}  Error listing fields: {e}")

    # Try common accessor patterns
    print(f"\n{indent}COMMON PATTERNS:")

    patterns = [
        ("toString", lambda: str(obj.toString())),
        ("size/length", lambda: obj.size() if hasattr(obj, 'size') else
                               obj.length() if hasattr(obj, 'length') else None),
        ("isEmpty", lambda: obj.isEmpty() if hasattr(obj, 'isEmpty') else None),
        ("iterator", lambda: obj.iterator() if hasattr(obj, 'iterator') else None),
    ]

    for pattern_name, pattern_func in patterns:
        try:
            result = pattern_func()
            if result is not None:
                print(f"{indent}  - {pattern_name}: {repr(result)[:80]}")
        except Exception as e:
            pass  # Pattern not applicable

    # Check if it's a collection/iterable
    print(f"\n{indent}COLLECTION ANALYSIS:")
    is_iterable = False

    try:
        if hasattr(obj, 'iterator'):
            print(f"{indent}  ✓ Has iterator() method")
            iterator = obj.iterator()
            print(f"{indent}    Iterator type: {type(iterator)}")
            is_iterable = True

            # Try to peek at first few elements
            if hasattr(iterator, 'hasNext') and iterator.hasNext():
                print(f"{indent}    Sample elements:")
                for i in range(min(3, 3)):  # First 3 elements
                    if iterator.hasNext():
                        element = iterator.next()
                        print(f"{indent}      [{i}] {type(element).__name__}: {repr(element)[:60]}")
                        if depth < max_depth - 1:
                            analyze_java_object(element, depth + 1, max_depth)
                    else:
                        break
    except Exception as e:
        print(f"{indent}  Iterator error: {e}")

    # Check if it's JPype array
    try:
        if jpype.isJArray(obj):
            print(f"{indent}  ✓ Is JPype array")
            print(f"{indent}    Length: {len(obj)}")
            print(f"{indent}    Element type: {obj.getClass().getComponentType().getName()}")
            is_iterable = True

            # Show first few elements
            print(f"{indent}    Sample elements:")
            for i in range(min(len(obj), 3)):
                element = obj[i]
                print(f"{indent}      [{i}] {type(element).__name__}: {repr(element)[:60]}")
    except Exception as e:
        pass

    # Check if it's a Map
    try:
        if hasattr(obj, 'entrySet'):
            print(f"{indent}  ✓ Is Map (has entrySet)")
            print(f"{indent}    Size: {obj.size()}")
            entries = obj.entrySet()
            print(f"{indent}    Sample entries:")
            for i, entry in enumerate(entries):
                if i >= 3:
                    break
                key = entry.getKey()
                value = entry.getValue()
                print(f"{indent}      {repr(key)[:30]} → {type(value).__name__}")
    except Exception as e:
        pass

    # Check for path-like objects
    print(f"\n{indent}PATH DETECTION:")
    is_path = False

    try:
        # java.nio.file.Path
        JavaPath = jpype.JClass("java.nio.file.Path")
        if isinstance(obj, JavaPath):
            print(f"{indent}  ✓ Is java.nio.file.Path")
            print(f"{indent}    Path: {obj.toAbsolutePath()}")
            is_path = True
    except:
        pass

    try:
        # java.io.File
        JavaFile = jpype.JClass("java.io.File")
        if isinstance(obj, JavaFile):
            print(f"{indent}  ✓ Is java.io.File")
            print(f"{indent}    Path: {obj.toPath()}")
            is_path = True
    except:
        pass

    # Suggest handling code
    print(f"\n{indent}SUGGESTED HANDLING:")
    if is_path:
        print(f"{indent}  Use: str(obj.toAbsolutePath()) or str(obj.toPath())")
    elif is_iterable:
        print(f"{indent}  Use: for item in obj.iterator(): ...")
        print(f"{indent}  Or: [item for item in obj]")
    else:
        print(f"{indent}  May need custom handling or str() conversion")


def generate_flatten_paths_code(obj):
    """Generate code snippet for _flatten_paths() to handle this type"""
    print("\n" + "=" * 70)
    print("SUGGESTED _flatten_paths() CODE")
    print("=" * 70)

    java_class_name = obj.getClass().getName()

    if hasattr(obj, 'toAbsolutePath'):
        print(f"""
# Handle {java_class_name}
try:
    java_path_class = jpype.JClass("{java_class_name}")
    if isinstance(obj, java_path_class):
        yield str(obj.toAbsolutePath())
        return
except RuntimeError:
    pass
""")
    elif hasattr(obj, 'iterator'):
        print(f"""
# Handle {java_class_name} (iterable)
if hasattr(obj, 'iterator'):
    iterator = obj.iterator()
    while iterator.hasNext():
        yield from visit(iterator.next())
    return
""")
    elif hasattr(obj, 'entrySet'):
        print(f"""
# Handle {java_class_name} (map)
if hasattr(obj, 'entrySet') and callable(obj.entrySet):
    for entry in obj.entrySet():
        yield from visit(entry.getValue())
    return
""")
    else:
        print(f"""
# Handle {java_class_name} (custom)
# TODO: Implement custom handling based on analysis above
try:
    # Try conversion to string
    path_str = str(obj)
    if path_str:
        yield path_str
except:
    pass
""")


if __name__ == "__main__":
    # Example usage - analyze a specific object
    print("Java Object Type Analyzer")
    print("=" * 70)

    # Start JVM and get object to analyze
    # Replace with your actual object acquisition code
    from pynf import NextflowEngine

    engine = NextflowEngine()
    script_path = engine.load_script("nextflow_scripts/file-output-process.nf")
    result = engine.execute(script_path)

    # Analyze different objects
    print("\n\nANALYZING: session.getWorkDir()")
    workdir = result.session.getWorkDir()
    analyze_java_object(workdir)
    generate_flatten_paths_code(workdir)

    # Add more objects as needed
    # print("\n\nANALYZING: <another object>")
    # analyze_java_object(another_object)
```

### 3. Run Analysis

Execute the analyzer on target objects:

```bash
uv run python analyze_types.py > type_analysis.txt
cat type_analysis.txt
```

### 4. Interpret Results

**Key information to extract:**

**For Path Objects:**

- Look for `toAbsolutePath()`, `toPath()`, `toString()` methods
- Check if instance of `java.nio.file.Path` or `java.io.File`
- Use: `str(obj.toAbsolutePath())`

**For Collections:**

- Check for `iterator()`, `size()`, `isEmpty()` methods
- Determine element type from sample elements
- Use: `for item in obj.iterator(): ...` or `[item for item in obj]`

**For Maps:**

- Look for `entrySet()`, `get()`, `keySet()` methods
- Check entry structure (getKey, getValue)
- Use: `for entry in obj.entrySet(): visit(entry.getValue())`

**For Unknown Types:**

- Check `toString()` output
- Look for accessor methods (get*, to*)
- Try conversion to Python types

### 5. Implement Handling Code

Add support to `src/pynf/result.py` in `_flatten_paths()`:

```python
def _flatten_paths(self, value):
    """Yield string paths extracted from nested Java/Python structures."""

    def visit(obj):
        if obj is None:
            return

        # Existing handlers...

        # NEW: Add handler for discovered type
        try:
            NewJavaClass = _java_class("com.example.NewClass")
            if isinstance(obj, NewJavaClass):
                # Use pattern discovered from analysis
                yield str(obj.toAbsolutePath())  # Or appropriate method
                return
        except RuntimeError:
            pass

        # Continue with other handlers...
```

### 6. Test New Handler

Create test to verify handling:

```python
def test_new_java_type_handling():
    """Test _flatten_paths handles NewJavaClass"""
    from pynf.result import NextflowResult

    # Create instance of new type
    # ... (however you obtain it) ...
    new_obj = ...

    # Test flattening
    result = NextflowResult(None, None, None)
    paths = list(result._flatten_paths(new_obj))

    assert len(paths) > 0, "Should extract paths"
    assert all(isinstance(p, str) for p in paths), "Should return strings"
```

## Common Java Type Patterns

### Pattern 1: java.nio.file.Path

**Characteristics:**

- Has `toAbsolutePath()`, `toString()` methods
- Represents file system paths

**Handling:**

```python
try:
    JavaPath = jpype.JClass("java.nio.file.Path")
    if isinstance(obj, JavaPath):
        yield str(obj.toAbsolutePath())
        return
except RuntimeError:
    pass
```

### Pattern 2: java.util.List

**Characteristics:**

- Has `iterator()`, `size()`, `get()` methods
- Iterable collection

**Handling:**

```python
if hasattr(obj, 'iterator'):
    iterator = obj.iterator()
    while iterator.hasNext():
        yield from visit(iterator.next())
    return
```

### Pattern 3: java.util.Map

**Characteristics:**

- Has `entrySet()`, `get()`, `keySet()` methods
- Key-value pairs

**Handling:**

```python
if hasattr(obj, 'entrySet') and callable(obj.entrySet):
    for entry in obj.entrySet():
        yield from visit(entry.getValue())
    return
```

### Pattern 4: Java Arrays

**Characteristics:**

- `jpype.isJArray(obj)` returns True
- Fixed-size indexed collection

**Handling:**

```python
if jpype.isJArray(obj):
    for item in obj:
        yield from visit(item)
    return
```

### Pattern 5: Custom Groovy Objects

**Characteristics:**

- May have dynamic properties
- Often have `getProperty()` method
- Need careful introspection

**Handling:**

```python
# Try common patterns
if hasattr(obj, 'getValue') and callable(obj.getValue):
    yield from visit(obj.getValue())
    return
```

## Example Analysis Sessions

### Session 1: Analyzing File Event Target

```python
# From observer
def onFilePublish(self, event):
    target = event.getTarget()
    analyze_java_object(target)

# Output shows:
# Java class: java.nio.file.UnixPath
# Methods: toAbsolutePath(), toString(), ...
# → Already handled by existing code
```

### Session 2: Unknown Collection Type

```python
workflow_output = result.get_workflow_outputs()[0]['value']
analyze_java_object(workflow_output)

# Output shows:
# Java class: groovy.util.NodeList
# Has iterator() method
# Elements are groovy.util.Node objects
# → Need to add NodeList handler
```

### Session 3: Nested Structure

```python
complex_obj = session.getBinding().getVariable("complex")
analyze_java_object(complex_obj, max_depth=4)

# Output shows multiple levels:
# Level 0: java.util.LinkedHashMap
# Level 1: Values are java.util.ArrayList
# Level 2: Elements are java.nio.file.Path
# → Existing handlers cover this recursively
```

## Integration with Development Workflow

**Usage workflow:**

1. Encounter unknown Java type in observer or result
2. Use this skill to analyze the type
3. Implement handler in `_flatten_paths()`
4. Test with `test-nextflow-module`
5. Add formal test with `create-integration-test`
6. Commit: `jj commit -m "Add support for JavaType"`

**When to use:**

- Implementing new observer handlers
- Supporting new Nextflow output patterns
- Debugging path extraction issues
- Extending result collection capabilities

## Related Skills

- **debug-observer-events**: Identify which Java types are causing issues
- **test-nextflow-module**: Test new handlers quickly
- **create-integration-test**: Add regression tests for new types

## Advanced Tips

**Comparing with Nextflow source:**

```bash
# Find Java class definition in Nextflow repo
cd nextflow
find . -name "*.java" -o -name "*.groovy" | xargs grep "class TargetClassName"
```

**Using JPype introspection:**

```python
# Get detailed method signatures
for method in obj.getClass().getMethods():
    if method.getName() == "target_method":
        print(f"Return type: {method.getReturnType()}")
        print(f"Parameters: {[p.getType() for p in method.getParameters()]}")
```

**Testing type checking:**

```python
# Verify isinstance works
JavaClass = jpype.JClass("full.class.Name")
assert isinstance(obj, JavaClass)
```
