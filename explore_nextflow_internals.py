"""
Explore Nextflow's internal representation of parsed scripts.
"""

from pathlib import Path
from pynf import NextflowEngine

# Initialize engine
engine = NextflowEngine()

# Load and parse samtools/view
script_path = Path("nf-core-modules/samtools/view/main.nf")

# We need to create a session and parse the script
import jpype
session = engine.Session()
ScriptFile = jpype.JClass("nextflow.script.ScriptFile")
ArrayList = jpype.JClass("java.util.ArrayList")

script_file = ScriptFile(jpype.java.nio.file.Paths.get(str(script_path)))
session.init(script_file, ArrayList(), None, None)
session.start()

# Parse the script
loader = engine.ScriptLoaderFactory.create(session)
java_path = jpype.java.nio.file.Paths.get(str(script_path))
loader.parse(java_path)
script = loader.getScript()

print("=" * 80)
print("SCRIPT OBJECT INSPECTION")
print("=" * 80)

# Get the script's class
script_class = script.getClass()
print(f"\nScript class: {script_class.getName()}")

# Check if it's a module
print(f"\nIs module script: {hasattr(script, 'isModule') and script.isModule()}")

# Get metadata
try:
    meta = script.getScriptMeta()
    print(f"\nScript metadata class: {meta.getClass().getName()}")

    # Try to get process definitions
    print("\n" + "=" * 80)
    print("PROCESS DEFINITIONS")
    print("=" * 80)

    # Get all methods
    for method in meta.getClass().getMethods():
        method_name = method.getName()
        if "process" in method_name.lower() or "input" in method_name.lower():
            print(f"  - {method_name}")

    # Try common methods
    if hasattr(meta, 'getProcessNames'):
        process_names = meta.getProcessNames()
        print(f"\nProcess names: {list(process_names)}")

    if hasattr(meta, 'getProcesses'):
        processes = meta.getProcesses()
        print(f"\nProcesses type: {type(processes)}")
        print(f"Processes: {processes}")

        # Iterate if it's a collection
        if hasattr(processes, 'values'):
            for proc_name, proc_def in processes.items():
                print(f"\n--- Process: {proc_name} ---")
                print(f"Process class: {proc_def.getClass().getName()}")

                # Try to get input definitions
                for method in proc_def.getClass().getMethods():
                    method_name = method.getName()
                    if "input" in method_name.lower():
                        try:
                            result = method.invoke(proc_def)
                            print(f"  {method_name}(): {result}")
                        except:
                            pass

except Exception as e:
    print(f"\nError inspecting metadata: {e}")
    import traceback
    traceback.print_exc()

# Try binding
print("\n" + "=" * 80)
print("SESSION BINDING")
print("=" * 80)

binding = session.getBinding()
print(f"Binding variables: {list(binding.getVariables().keySet())}")

# Try to get process from binding
if binding.hasVariable('SAMTOOLS_VIEW'):
    samtools_view = binding.getVariable('SAMTOOLS_VIEW')
    print(f"\nSAMTOOLS_VIEW type: {type(samtools_view)}")
    print(f"SAMTOOLS_VIEW class: {samtools_view.getClass().getName()}")

    # Try to inspect
    for method in samtools_view.getClass().getMethods():
        method_name = method.getName()
        if "input" in method_name.lower() or "In" in method_name:
            print(f"  - {method_name}")

session.destroy()
print("\n" + "=" * 80)
