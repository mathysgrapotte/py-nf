"""
Extract input channel definitions from Groovy AST.
"""

from pathlib import Path
import jpype

# Start JVM if not already started
if not jpype.isJVMStarted():
    jar_path = "nextflow/build/releases/nextflow-25.10.0-one.jar"
    jpype.startJVM(classpath=[jar_path])

# Import Groovy AST classes
CompilerConfiguration = jpype.JClass("org.codehaus.groovy.control.CompilerConfiguration")
CompilationUnit = jpype.JClass("org.codehaus.groovy.control.CompilationUnit")
GroovyClassLoader = jpype.JClass("groovy.lang.GroovyClassLoader")
Phases = jpype.JClass("org.codehaus.groovy.control.Phases")

# Read the .nf file
script_path = Path("nf-core-modules/samtools/view/main.nf")
nf_content = script_path.read_text()

# Configure and compile
config = CompilerConfiguration()
config.setScriptBaseClass("nextflow.script.BaseScript")
classLoader = GroovyClassLoader()
unit = CompilationUnit(config, None, classLoader)
unit.addSource(str(script_path), nf_content)
unit.compile(Phases.CONVERSION)

# Get the AST
ast = unit.getAST()
modules = ast.getModules()
module = modules[0]
classes = module.getClasses()
cls_node = classes[0]

# Find the run() method
run_method = None
for method in cls_node.getMethods():
    if str(method.getName()) == 'run':
        run_method = method
        break

if not run_method:
    print("No run() method found")
    exit(1)

# Get the block statement from run()
code = run_method.getCode()
if not hasattr(code, 'getStatements'):
    print("run() doesn't have statements")
    exit(1)

run_statements = code.getStatements()

# The run() method calls process(SAMTOOLS_VIEW { ... })
# We need to find the closure inside
print("=" * 80)
print("FINDING PROCESS CLOSURE")
print("=" * 80)

process_closure = None
for stmt in run_statements:
    if hasattr(stmt, 'getExpression'):
        expr = stmt.getExpression()
        expr_class = expr.getClass().getName()

        if 'MethodCallExpression' in expr_class:
            method = expr.getMethod()
            if str(method.getText()) == 'process':
                # Found process() call, get its arguments
                args = expr.getArguments()
                for arg in args:
                    arg_class = arg.getClass().getName()
                    if 'MethodCallExpression' in arg_class:
                        # This is SAMTOOLS_VIEW(...), get its argument (the closure)
                        samtools_args = arg.getArguments()
                        for samtools_arg in samtools_args:
                            samtools_arg_class = samtools_arg.getClass().getName()
                            if 'ClosureExpression' in samtools_arg_class:
                                process_closure = samtools_arg
                                print(f"✓ Found process closure: {samtools_arg_class}")
                                break

if not process_closure:
    print("✗ Could not find process closure")
    exit(1)

# Get statements from the closure
closure_code = process_closure.getCode()
statements = closure_code.getStatements()

print(f"✓ Found {len(statements)} statements in closure")

print("\n" + "=" * 80)
print("EXTRACTING INPUT CHANNELS")
print("=" * 80)

# Look for input declarations
# Inputs come before outputs, and they're method calls like tuple(), val(), path()
input_methods = {'tuple', 'val', 'path', 'file', 'env', 'stdin', 'each'}
output_methods = {'emit'}  # Outputs have 'emit' keyword

input_channels = []
found_output = False

def extract_variable_name(expr):
    """Extract variable name from an expression."""
    expr_class = expr.getClass().getName()
    if 'VariableExpression' in expr_class:
        return str(expr.getName())
    return None

def extract_input_params(method_call):
    """Extract parameter names from a method call (val, path, tuple, etc.)."""
    method_name = str(method_call.getMethod().getText())
    args = method_call.getArguments()

    params = []

    # If it's a tuple, iterate through its arguments
    if method_name == 'tuple':
        for arg in args:
            arg_class = arg.getClass().getName()
            if 'MethodCallExpression' in arg_class:
                # Nested val() or path() call
                nested_params = extract_input_params(arg)
                params.extend(nested_params)
    else:
        # Single parameter (val, path, etc.)
        for arg in args:
            var_name = extract_variable_name(arg)
            if var_name:
                params.append({'type': method_name, 'name': var_name})

    return params

for stmt in statements:
    stmt_class = stmt.getClass().getName()

    if 'ExpressionStatement' not in stmt_class:
        continue

    expr = stmt.getExpression()
    expr_class = expr.getClass().getName()

    if 'MethodCallExpression' not in expr_class:
        continue

    # Get method name
    method = expr.getMethod()
    method_text = str(method.getText())

    # Check if it's an output (has emit)
    args = expr.getArguments()
    for arg in args:
        if hasattr(arg, 'getClass') and 'MapExpression' in arg.getClass().getName():
            # Check for 'emit' key
            entries = arg.getMapEntryExpressions()
            for entry in entries:
                key = entry.getKeyExpression()
                if hasattr(key, 'getText') and str(key.getText()) == 'emit':
                    found_output = True
                    break

    if found_output:
        break  # Stop at first output

    # Check if it's an input method
    if method_text in input_methods:
        params = extract_input_params(expr)

        channel_info = {
            'type': method_text,
            'params': params
        }
        input_channels.append(channel_info)

        print(f"\nChannel {len(input_channels) - 1}: {method_text}")
        for p in params:
            print(f"  - {p['type']}({p['name']})")

print("\n" + "=" * 80)
print("RESULT")
print("=" * 80)
print(f"\nFound {len(input_channels)} input channels")

for i, channel in enumerate(input_channels):
    param_names = [p['name'] for p in channel['params']]
    print(f"Channel {i}: {channel['type']} -> {param_names}")
