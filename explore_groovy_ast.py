"""
Use Groovy's AST parser to extract process input definitions.
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
SourceUnit = jpype.JClass("org.codehaus.groovy.control.SourceUnit")
Phases = jpype.JClass("org.codehaus.groovy.control.Phases")

print("=" * 80)
print("GROOVY AST PARSING")
print("=" * 80)

# Read the .nf file
script_path = Path("nf-core-modules/samtools/view/main.nf")
nf_content = script_path.read_text()

print(f"\nParsing: {script_path}")
print(f"Content length: {len(nf_content)} chars")

# Configure compiler
config = CompilerConfiguration()
config.setScriptBaseClass("nextflow.script.BaseScript")

# Create compilation unit
classLoader = GroovyClassLoader()
unit = CompilationUnit(config, None, classLoader)

# Add source
unit.addSource(str(script_path), nf_content)

# Compile to AST (stop before class generation)
print("\nCompiling to AST...")
try:
    unit.compile(Phases.CONVERSION)  # Stop at AST phase
    print("✓ Compiled to AST successfully")
except Exception as e:
    print(f"✗ Compilation failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Get the AST
print("\n" + "=" * 80)
print("EXPLORING AST")
print("=" * 80)

# Get all class nodes (the script is compiled to a class)
ast = unit.getAST()
print(f"\nAST type: {type(ast)}")
print(f"AST: {ast}")

# Try to get modules
if hasattr(ast, 'getModules'):
    modules = ast.getModules()
    print(f"\nModules: {modules}")
    print(f"Module count: {len(modules) if hasattr(modules, '__len__') else 'N/A'}")

    for i, module in enumerate(modules):
        print(f"\n--- Module {i} ---")
        print(f"  Type: {type(module)}")
        print(f"  Class: {module.getClass().getName()}")

        # Get class nodes
        if hasattr(module, 'getClasses'):
            classes = module.getClasses()
            print(f"  Classes: {len(classes) if hasattr(classes, '__len__') else classes}")

            for cls_node in classes:
                print(f"\n  --- ClassNode ---")
                print(f"    Name: {cls_node.getName()}")
                print(f"    Methods: {cls_node.getMethods().size() if hasattr(cls_node.getMethods(), 'size') else len(cls_node.getMethods())}")

                # Iterate through methods
                for method in cls_node.getMethods():
                    method_name = str(method.getName())
                    print(f"\n    Method: {method_name}")

                    # Check if this looks like a process definition
                    if method_name.startswith('$') or method_name == 'run':
                        print(f"      Code: {method.getCode()}")

                        # Try to get statement
                        code = method.getCode()
                        if code:
                            print(f"      Code type: {code.getClass().getName()}")

                            # If it's a block statement, explore statements
                            if hasattr(code, 'getStatements'):
                                stmts = code.getStatements()
                                print(f"      Statements: {len(stmts) if hasattr(stmts, '__len__') else stmts}")

                                for stmt_idx, stmt in enumerate(stmts):
                                    if stmt_idx > 5:
                                        print(f"      ... ({len(stmts) - 5} more statements)")
                                        break
                                    print(f"      [{stmt_idx}]: {stmt.getClass().getName()}")
                                    print(f"           Text: {stmt.getText()}")

print("\n" + "=" * 80)
print("CONCLUSION")
print("=" * 80)
print("Can we extract process input definitions from Groovy AST?")
