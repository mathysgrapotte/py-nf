"""
Check what's available in the parsed AST before script execution.
"""

from pathlib import Path
from pynf import NextflowEngine
import jpype

engine = NextflowEngine()
session = engine.Session()
ScriptFile = jpype.JClass("nextflow.script.ScriptFile")
ArrayList = jpype.JClass("java.util.ArrayList")

script_path = Path("nf-core-modules/samtools/view/main.nf")
script_file = ScriptFile(jpype.java.nio.file.Paths.get(str(script_path)))
session.init(script_file, ArrayList(), None, None)
session.start()

# Parse script (but DON'T execute)
loader = engine.ScriptLoaderFactory.create(session)
java_path = jpype.java.nio.file.Paths.get(str(script_path))
loader.parse(java_path)
script = loader.getScript()

print("=" * 80)
print("AFTER PARSE, BEFORE EXECUTION")
print("=" * 80)

# Check loader
print("\nLOADER:")
print(f"  Type: {type(loader)}")
print(f"  Class: {loader.getClass().getName()}")

loader_methods = []
for method in loader.getClass().getMethods():
    method_name = str(method.getName())
    if any(kw in method_name.lower() for kw in ['process', 'meta', 'def', 'input']):
        loader_methods.append(method_name)

print(f"\nInteresting loader methods:")
for m in sorted(set(loader_methods)):
    print(f"  - {m}")

# Try to get metadata from loader
for method_name in ['getScriptMeta', 'getMeta', 'getMetadata', 'getProcessDefinitions']:
    if hasattr(loader, method_name):
        try:
            result = getattr(loader, method_name)()
            print(f"\n{method_name}(): {result}")
        except Exception as e:
            print(f"\n{method_name}() failed: {e}")

# Check script object itself
print("\n" + "=" * 80)
print("SCRIPT OBJECT")
print("=" * 80)

# Try to access process as a method/property
script_meta = script.getMetaClass()
print(f"\nMetaClass: {script_meta}")

# Get all properties/methods
try:
    properties = script_meta.getProperties()
    print(f"\nScript properties: {len(properties)}")
    for prop in properties:
        prop_name = str(prop.getName())
        if 'samtools' in prop_name.lower() or 'process' in prop_name.lower():
            print(f"  - {prop_name}")
except Exception as e:
    print(f"Error getting properties: {e}")

# Try to call SAMTOOLS_VIEW directly on script (it's defined as a method)
print("\n" + "=" * 80)
print("TRYING TO ACCESS PROCESS DEFINITION DIRECTLY")
print("=" * 80)

try:
    # In Groovy, a process definition becomes a method/closure on the script
    if hasattr(script, 'SAMTOOLS_VIEW'):
        process_def = script.SAMTOOLS_VIEW
        print(f"✓ Found SAMTOOLS_VIEW on script!")
        print(f"  Type: {type(process_def)}")
        print(f"  Class: {process_def.getClass().getName()}")

        # Try to inspect it
        for method_name in dir(process_def):
            if 'input' in method_name.lower():
                print(f"  Method: {method_name}")
    else:
        print("✗ SAMTOOLS_VIEW not accessible on script")
except Exception as e:
    print(f"Error: {e}")

session.destroy()
print("\n" + "=" * 80)
print("CONCLUSION: Can we get inputs before execution?")
print("=" * 80)
