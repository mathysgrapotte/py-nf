"""
Deeper exploration of Nextflow process input handling.
"""

from pathlib import Path
from pynf import NextflowEngine
import jpype

# Initialize engine
engine = NextflowEngine()

# Create session
session = engine.Session()
ScriptFile = jpype.JClass("nextflow.script.ScriptFile")
ArrayList = jpype.JClass("java.util.ArrayList")

script_path = Path("nf-core-modules/samtools/view/main.nf")
script_file = ScriptFile(jpype.java.nio.file.Paths.get(str(script_path)))
session.init(script_file, ArrayList(), None, None)
session.start()

# Parse script
loader = engine.ScriptLoaderFactory.create(session)
java_path = jpype.java.nio.file.Paths.get(str(script_path))
loader.parse(java_path)
script = loader.getScript()

print("=" * 80)
print("EXPLORING SCRIPT OBJECT")
print("=" * 80)

# Check all methods on script
script_class = script.getClass()
print(f"\nScript class: {script_class.getName()}")

interesting_methods = []
for method in script_class.getMethods():
    method_name = str(method.getName())
    if any(keyword in method_name.lower() for keyword in ['process', 'meta', 'def', 'run', 'get']):
        interesting_methods.append(method_name)

print(f"\nInteresting methods ({len(interesting_methods)}):")
for m in sorted(set(interesting_methods))[:30]:
    print(f"  - {m}")

# Try to execute the script to populate binding
print("\n" + "=" * 80)
print("EXECUTING SCRIPT TO POPULATE BINDING")
print("=" * 80)

try:
    loader.runScript()
    print("✓ Script executed")
except Exception as e:
    print(f"✗ Error executing: {e}")

binding = session.getBinding()
print(f"\nBinding variables after execution: {list(binding.getVariables().keySet())}")

# Check if process is now in binding
if binding.hasVariable('SAMTOOLS_VIEW'):
    print("\n✓ Found SAMTOOLS_VIEW in binding!")

    samtools_view = binding.getVariable('SAMTOOLS_VIEW')
    proc_class = samtools_view.getClass()
    print(f"Process class: {proc_class.getName()}")

    # List all methods
    print("\nProcess methods:")
    for method in proc_class.getMethods():
        method_name = method.getName()
        if any(keyword in method_name.lower() for keyword in ['input', 'param', 'in', 'get', 'decl']):
            print(f"  - {method_name}")

    # Try to get inputs
    print("\n" + "=" * 80)
    print("EXTRACTING INPUT INFORMATION")
    print("=" * 80)

    # Try different approaches
    approaches = [
        ('getInputs', []),
        ('getDeclaredInputs', []),
        ('getInputsList', []),
        ('getConfig', []),
        ('getProcessConfig', []),
    ]

    for method_name, args in approaches:
        try:
            if hasattr(samtools_view, method_name):
                method = getattr(samtools_view, method_name)
                result = method(*args)
                print(f"\n{method_name}():")
                print(f"  Type: {type(result)}")
                print(f"  Value: {result}")

                # If it's a collection, explore it
                if hasattr(result, '__iter__') and not isinstance(result, str):
                    print(f"  Length: {len(result) if hasattr(result, '__len__') else 'N/A'}")
                    if hasattr(result, '__iter__'):
                        for i, item in enumerate(result):
                            print(f"  [{i}]: {item} (type: {type(item).__name__})")
                            if hasattr(item, 'getName'):
                                print(f"       name: {item.getName()}")
                            if i >= 5:
                                print(f"  ... ({len(result) - 5} more)")
                                break
        except Exception as e:
            pass

# Alternative: Look in session for process registry
print("\n" + "=" * 80)
print("LOOKING FOR PROCESS REGISTRY IN SESSION")
print("=" * 80)

session_class = session.getClass()
for method in session_class.getMethods():
    method_name = str(method.getName())
    if 'process' in method_name.lower():
        print(f"  - {method_name}")

# Explore processRegister
print("\n" + "=" * 80)
print("EXPLORING PROCESS REGISTER")
print("=" * 80)

# Try to access registered processes
try:
    # Check if there's a field for processes
    session_fields = session.getClass().getDeclaredFields()
    print(f"\nSession fields:")
    for field in session_fields:
        field_name = str(field.getName())
        if 'process' in field_name.lower():
            print(f"  - {field_name}")
            field.setAccessible(True)
            try:
                value = field.get(session)
                print(f"      Type: {type(value)}")
                print(f"      Value: {value}")
                if hasattr(value, 'size'):
                    print(f"      Size: {value.size()}")
                if hasattr(value, 'keySet'):
                    print(f"      Keys: {list(value.keySet())}")
            except Exception as e:
                print(f"      Error accessing: {e}")
except Exception as e:
    print(f"Error exploring fields: {e}")

session.destroy()
print("\n" + "=" * 80)
print("DONE")
print("=" * 80)
