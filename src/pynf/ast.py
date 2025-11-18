"""
Nextflow AST extraction using JPype and Nextflow's Java API.
"""

import json
from pathlib import Path
from typing import Any, Dict
import jpype
import yaml


def parse_nf_file(file_path: str | Path) -> Dict[str, Any]:
    """
    Parse a Nextflow file and return its full AST as a Python dict.

    Args:
        file_path: Path to .nf file

    Returns:
        Dictionary representation of the full Groovy AST
    """
    from pynf.engine import NextflowEngine

    file_path = Path(file_path)
    engine = NextflowEngine()

    # Set up Nextflow session
    Session = jpype.JClass("nextflow.Session")
    ScriptFile = jpype.JClass("nextflow.script.ScriptFile")
    ArrayList = jpype.JClass("java.util.ArrayList")

    session = Session()
    script_file = ScriptFile(jpype.java.nio.file.Paths.get(str(file_path)))
    session.init(script_file, ArrayList(), None, None)
    session.start()

    # Use ScriptCompiler to get AST
    ScriptCompiler = jpype.JClass("nextflow.script.parser.v2.ScriptCompiler")
    compiler = ScriptCompiler(False, None, session.getClassLoader())

    # Compile and get sources
    compiler.compile(jpype.java.io.File(str(file_path)))
    sources = compiler.getSources()

    # Get AST from first source unit
    source = next(iter(sources))
    ast = source.getAST()

    # Convert to Python dict
    result = ast_to_dict(ast)

    session.destroy()
    return result


def ast_to_dict(node: Any) -> Any:
    """
    Recursively convert Java AST node to Python dict.

    Args:
        node: Java AST node

    Returns:
        Python dict/list/primitive representation
    """
    if node is None:
        return None

    # Handle primitives
    if isinstance(node, (str, int, float, bool)):
        return node

    # Load Java classes for type checking
    JavaString = jpype.JClass("java.lang.String")
    JavaList = jpype.JClass("java.util.List")
    JavaMap = jpype.JClass("java.util.Map")
    ASTNode = jpype.JClass("org.codehaus.groovy.ast.ASTNode")
    ModuleNode = jpype.JClass("org.codehaus.groovy.ast.ModuleNode")
    ClassNode = jpype.JClass("org.codehaus.groovy.ast.ClassNode")
    MethodNode = jpype.JClass("org.codehaus.groovy.ast.MethodNode")
    BlockStatement = jpype.JClass("org.codehaus.groovy.ast.stmt.BlockStatement")
    ExpressionStatement = jpype.JClass("org.codehaus.groovy.ast.stmt.ExpressionStatement")
    VariableExpression = jpype.JClass("org.codehaus.groovy.ast.expr.VariableExpression")
    MethodCallExpression = jpype.JClass("org.codehaus.groovy.ast.expr.MethodCallExpression")
    ConstantExpression = jpype.JClass("org.codehaus.groovy.ast.expr.ConstantExpression")

    # Handle Java strings - convert to Python str
    if isinstance(node, JavaString):
        return str(node)

    # Handle Java collections
    if isinstance(node, JavaList):
        return [ast_to_dict(item) for item in node]

    if isinstance(node, JavaMap):
        result = {}
        for key in node.keySet():
            result[str(key)] = ast_to_dict(node.get(key))
        return result

    # Handle AST nodes
    node_dict = {"_type": str(node.getClass().getSimpleName())}

    # Add text representation if available
    if isinstance(node, ASTNode):
        if hasattr(node, 'getText'):
            node_dict["text"] = str(node.getText())

    # Handle specific node types
    if isinstance(node, ModuleNode):
        node_dict["classes"] = [ast_to_dict(cls) for cls in node.getClasses()]
        node_dict["imports"] = [ast_to_dict(imp) for imp in node.getImports()]
        node_dict["methods"] = [ast_to_dict(method) for method in node.getMethods()]
        if node.getStatementBlock():
            node_dict["statementBlock"] = ast_to_dict(node.getStatementBlock())

    elif isinstance(node, ClassNode):
        node_dict["name"] = str(node.getName())
        node_dict["methods"] = [ast_to_dict(m) for m in node.getMethods()]
        node_dict["fields"] = [ast_to_dict(f) for f in node.getFields()]
        if node.getSuperClass():
            node_dict["superClass"] = str(node.getSuperClass().getName())

    elif isinstance(node, MethodNode):
        node_dict["name"] = str(node.getName())
        node_dict["parameters"] = [ast_to_dict(p) for p in node.getParameters()]
        if node.getCode():
            node_dict["code"] = ast_to_dict(node.getCode())

    elif isinstance(node, BlockStatement):
        node_dict["statements"] = [ast_to_dict(s) for s in node.getStatements()]

    elif isinstance(node, ExpressionStatement):
        node_dict["expression"] = ast_to_dict(node.getExpression())

    elif isinstance(node, VariableExpression):
        node_dict["variable"] = str(node.getName())

    elif isinstance(node, MethodCallExpression):
        node_dict["methodName"] = str(node.getMethodAsString())
        node_dict["objectExpression"] = ast_to_dict(node.getObjectExpression())
        node_dict["arguments"] = ast_to_dict(node.getArguments())

    elif isinstance(node, ConstantExpression):
        node_dict["value"] = str(node.getValue())

    return node_dict


def print_ast(ast_dict: Dict[str, Any], indent: int = 0, max_depth: int = 10):
    """
    Pretty-print AST dictionary.

    Args:
        ast_dict: AST dictionary from ast_to_dict()
        indent: Current indentation level
        max_depth: Maximum depth to print
    """
    if indent > max_depth:
        print("  " * indent + "...")
        return

    if isinstance(ast_dict, dict):
        node_type = ast_dict.get("_type", "Unknown")
        name = ast_dict.get("name", ast_dict.get("variable", ""))

        header = f"{node_type}"
        if name:
            header += f" '{name}'"

        print("  " * indent + header)

        for key, value in ast_dict.items():
            if key in ["_type", "name", "variable"]:
                continue

            if isinstance(value, (dict, list)):
                print("  " * (indent + 1) + f"{key}:")
                print_ast(value, indent + 2, max_depth)
            else:
                print("  " * (indent + 1) + f"{key}: {value}")

    elif isinstance(ast_dict, list):
        for item in ast_dict:
            print_ast(item, indent, max_depth)


def export_ast(ast_dict: Dict[str, Any], output_path: str | Path):
    """
    Export AST to JSON or YAML file.

    Args:
        ast_dict: AST dictionary from ast_to_dict()
        output_path: Output file path (.json or .yaml/.yml)
    """
    output_path = Path(output_path)

    if output_path.suffix in [".yaml", ".yml"]:
        with open(output_path, "w") as f:
            yaml.dump(ast_dict, f, default_flow_style=False, sort_keys=False)
    else:
        with open(output_path, "w") as f:
            json.dump(ast_dict, f, indent=2)
