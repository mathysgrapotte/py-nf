"""
Agent tools for Nextflow workflow operations.

Provides Tool classes that wrap pynf functionality for use with smolagents.
"""

import json
import os
import yaml
from pathlib import Path
from typing import Optional, List, Dict, Any

from smolagents import Tool
import pynf
from pynf import tools as pynf_tools


class ListNFCoreModulesTool(Tool):
    """Lists available nf-core modules that can be downloaded and executed."""

    name = "list_nfcore_modules"
    description = """
    Lists all available nf-core bioinformatics modules.

    Use this to discover what modules are available for bioinformatics analysis.
    Returns a list of module names organized by category.

    No inputs required.
    """
    inputs = {}
    output_type = "string"

    def forward(self) -> str:
        """List available nf-core modules."""
        try:
            modules = pynf_tools.list_modules()

            if not modules:
                return "No modules available. Check your internet connection."

            # Format as readable text (just show count and some examples)
            output = f"Available nf-core modules: {len(modules)} total\n\n"
            output += "Sample modules:\n"
            for module in modules[:20]:
                output += f"  - {module}\n"

            if len(modules) > 20:
                output += f"\n... and {len(modules) - 20} more modules.\n"

            output += "\nUse 'list_submodules' to see submodules for a specific module.\n"
            output += "Use 'get_module_info' to see detailed information about a module.\n"

            return output
        except Exception as e:
            return f"Error listing modules: {e}"


class ListSubmodulesTool(Tool):
    """Lists submodules available within a specific nf-core module."""

    name = "list_submodules"
    description = """
    Lists all submodules available for a given nf-core module.

    For example, 'samtools' may contain submodules like 'view', 'sort', 'index', etc.
    Use this before downloading to see what specific submodules are available.

    Input:
    - module_name: Name of the module (e.g., 'samtools', 'bcftools')
    """
    inputs = {
        "module_name": {
            "type": "string",
            "description": "Name of the nf-core module (e.g., 'samtools')"
        }
    }
    output_type = "string"

    def forward(self, module_name: str) -> str:
        """List submodules."""
        try:
            submodules = pynf_tools.list_submodules(module_name)

            if not submodules:
                return f"Module '{module_name}' has no submodules. Use 'get_module_info' to download and inspect it."

            output = f"Submodules for {module_name}:\n\n"
            for submodule in submodules:
                output += f"  - {module_name}/{submodule}\n"

            output += f"\nUse 'get_module_info' with the full path (e.g., '{module_name}/{submodules[0]}') to see details.\n"

            return output
        except Exception as e:
            return f"Error listing submodules: {e}"


class GetModuleInfoTool(Tool):
    """Downloads an nf-core module and shows its metadata from meta.yml."""

    name = "get_module_info"
    description = """
    Downloads an nf-core module (if not already cached) and displays its metadata.

    This shows the module's description, inputs, outputs, and other metadata from meta.yml.
    Use this to understand what a module does and what inputs it requires before running it.

    Input:
    - module_name: Full module name including submodule (e.g., 'fastqc', 'samtools/view')
    """
    inputs = {
        "module_name": {
            "type": "string",
            "description": "Full module name with submodule (e.g., 'fastqc', 'samtools/view')"
        }
    }
    output_type = "string"

    def forward(self, module_name: str) -> str:
        """Get module information by downloading and parsing meta.yml."""
        try:
            # Use existing inspect_module function which downloads and parses meta.yml
            info = pynf_tools.inspect_module(module_name)

            output = f"Module: {module_name}\n"
            output += f"Location: {info['path']}\n\n"

            # Parse meta information
            meta = info['meta']

            # Show key sections
            if 'name' in meta:
                output += f"Name: {meta['name']}\n"

            if 'description' in meta:
                output += f"Description: {meta['description']}\n\n"

            if 'keywords' in meta:
                output += f"Keywords: {', '.join(meta['keywords'])}\n\n"

            # Show tools
            if 'tools' in meta:
                output += "Tools:\n"
                for tool in meta['tools']:
                    for tool_name, tool_info in tool.items():
                        output += f"  - {tool_name}\n"
                        if 'description' in tool_info:
                            output += f"    {tool_info['description']}\n"
                output += "\n"

            # Show inputs - this is critical for the agent
            if 'input' in meta:
                output += "Inputs:\n"
                for input_group in meta['input']:
                    # Input groups are nested lists in nf-core meta.yml
                    if isinstance(input_group, list):
                        for input_item in input_group:
                            if isinstance(input_item, dict):
                                for input_name, input_info in input_item.items():
                                    output += f"  - {input_name}:\n"
                                    if isinstance(input_info, dict):
                                        if 'type' in input_info:
                                            output += f"    type: {input_info['type']}\n"
                                        if 'description' in input_info:
                                            desc = input_info['description'].strip()
                                            output += f"    description: {desc}\n"
                                        if 'pattern' in input_info:
                                            output += f"    pattern: {input_info['pattern']}\n"
                output += "\n"

            # Show outputs
            if 'output' in meta:
                output += "Outputs:\n"
                for output_name, output_content in meta['output'].items():
                    output += f"  - {output_name}:\n"
                    if isinstance(output_content, list) and len(output_content) > 0:
                        # Get the first item which contains the actual output spec
                        if isinstance(output_content[0], list) and len(output_content[0]) > 1:
                            output_spec = output_content[0][1]
                            if isinstance(output_spec, dict):
                                for pattern, info in output_spec.items():
                                    if isinstance(info, dict):
                                        if 'type' in info:
                                            output += f"    type: {info['type']}\n"
                                        if 'description' in info:
                                            output += f"    description: {info['description']}\n"
                                        if 'pattern' in info:
                                            output += f"    pattern: {info['pattern']}\n"
                output += "\n"

            output += "\nModule is ready to run. Use 'run_nf_module' to execute it.\n"

            return output
        except Exception as e:
            return f"Error getting module info: {e}"


class RunNFModuleTool(Tool):
    """Executes an nf-core module with specified inputs and parameters."""

    name = "run_nf_module"
    description = """
    Executes a Nextflow module with provided inputs and parameters.

    This is the main tool for running bioinformatics analyses.
    Docker is enabled by default with nf-core registry (quay.io).

    IMPORTANT - Input Format:
    The 'inputs' parameter must be a JSON string representing a list of dictionaries,
    where each dictionary corresponds to one input channel group.

    Example for a tool that takes paired-end reads:
    inputs = '[{"meta": {"id": "sample1"}, "reads": ["read1.fq", "read2.fq"]}]'

    Example for fastqc (single-end reads):
    inputs = '[{"meta": {"id": "sample1"}, "reads": ["sample.fastq"]}]'

    Example for samtools/view (requires BAM and optional index):
    inputs = '[{"meta": {"id": "sample1"}, "input": ["sample.bam"], "index": []}]'

    The meta dictionary typically contains an "id" field to identify the sample.

    Inputs:
    - module_name: Name of the module (e.g., 'fastqc', 'samtools/view')
    - inputs: JSON string of input channel data (see format above)
    - params: Optional JSON string of parameters (e.g., '{"quality_threshold": 20}')
    - use_docker: Whether to use Docker for execution (default: true for nf-core modules)
    """
    inputs = {
        "module_name": {
            "type": "string",
            "description": "Name of the nf-core module to run"
        },
        "inputs": {
            "type": "string",
            "description": "JSON string of input data as list of dicts"
        },
        "params": {
            "type": "string",
            "description": "Optional JSON string of parameters",
            "nullable": True
        },
        "use_docker": {
            "type": "boolean",
            "description": "Use Docker for execution (default: true)",
            "nullable": True
        }
    }
    output_type = "string"

    def __init__(self, session_context=None):
        """Initialize with optional session context for tracking executions."""
        super().__init__()
        self.session_context = session_context

    def forward(
        self,
        module_name: str,
        inputs: str,
        params: Optional[str] = None,
        use_docker: bool = True
    ) -> str:
        """Run a Nextflow module."""
        try:
            # Parse inputs JSON
            try:
                inputs_data = json.loads(inputs)
            except json.JSONDecodeError as e:
                return f"Error: Invalid JSON in inputs parameter: {e}"

            # Parse params JSON if provided
            params_data = None
            if params:
                try:
                    params_data = json.loads(params)
                except json.JSONDecodeError as e:
                    return f"Error: Invalid JSON in params parameter: {e}"

            # Prepare module path
            modules_dir = Path("nf-core-modules")
            module_path = modules_dir / module_name / "main.nf"

            if not module_path.exists():
                return f"Module not found: {module_name}. Please use 'get_module_info' to download it first.\nLooking for: {module_path}"

            # Configure Docker with nf-core defaults
            docker_config = None
            if use_docker:
                docker_config = {
                    'enabled': True,
                    'registry': 'quay.io',  # Required for nf-core modules
                    'remove': True,  # Auto-remove container after execution
                }

            # Execute module
            result = pynf.run_module(
                nf_file=str(module_path),
                inputs=inputs_data,
                params=params_data,
                docker_config=docker_config,
                verbose=False
            )

            # Get outputs
            output_files = result.get_output_files()

            # Record execution in session context if available
            execution_id = None
            if self.session_context:
                execution_id = self.session_context.add_execution(
                    module=module_name,
                    inputs=inputs_data,
                    params=params_data,
                    outputs=output_files,
                    status="success"
                )

            # Format response
            output = f"Successfully executed module: {module_name}\n\n"

            if execution_id is not None:
                output += f"Execution ID: {execution_id}\n\n"

            output += f"Output files ({len(output_files)}):\n"
            for file_path in output_files:
                output += f"  - {file_path}\n"

            # Include execution report if available
            report = result.get_execution_report()
            if report:
                output += f"\nExecution summary:\n"
                output += f"  Completed tasks: {report.get('completed_count', 0)}\n"

            return output

        except Exception as e:
            # Record failure in session context
            if self.session_context:
                self.session_context.add_execution(
                    module=module_name,
                    inputs=inputs_data if 'inputs_data' in locals() else None,
                    params=params_data if 'params_data' in locals() else None,
                    status="failed",
                    error=str(e)
                )

            return f"Error executing module: {e}\n\nPlease check that:\n1. The module is downloaded (use 'get_module_info')\n2. Input files exist\n3. Input format matches module requirements"


class ListOutputFilesTool(Tool):
    """Lists output files from previous module executions."""

    name = "list_output_files"
    description = """
    Lists output files from a previous module execution.

    Use this to see what files were produced by a module run, so you can
    use them as inputs to subsequent modules.

    Input:
    - execution_id: Optional execution ID (if not provided, shows latest execution)
    """
    inputs = {
        "execution_id": {
            "type": "integer",
            "description": "Execution ID to get outputs for (optional, defaults to latest)",
            "nullable": True
        }
    }
    output_type = "string"

    def __init__(self, session_context=None):
        """Initialize with session context for accessing execution history."""
        super().__init__()
        self.session_context = session_context

    def forward(self, execution_id: Optional[int] = None) -> str:
        """List output files from an execution."""
        if not self.session_context:
            return "Error: No session context available."

        try:
            if execution_id is not None:
                record = self.session_context.get_execution(execution_id)
                if not record:
                    return f"No execution found with ID: {execution_id}"
            else:
                record = self.session_context.get_latest_execution()
                if not record:
                    return "No executions have been run yet."

            output = f"Execution ID: {record['id']}\n"
            output += f"Module: {record['module']}\n"
            output += f"Status: {record['status']}\n"
            output += f"Timestamp: {record['timestamp']}\n\n"

            outputs = record.get('outputs', [])
            if outputs:
                output += f"Output files ({len(outputs)}):\n"
                for file_path in outputs:
                    output += f"  - {file_path}\n"
            else:
                output += "No output files recorded.\n"

            return output
        except Exception as e:
            return f"Error listing outputs: {e}"


class ReadFileTool(Tool):
    """Reads the contents of a file."""

    name = "read_file"
    description = """
    Reads and returns the contents of a file.

    Use this to inspect output files from module executions, such as
    quality control reports, log files, or other text outputs.

    Input:
    - file_path: Path to the file to read
    - max_lines: Maximum number of lines to read (default: 100)
    """
    inputs = {
        "file_path": {
            "type": "string",
            "description": "Path to the file to read"
        },
        "max_lines": {
            "type": "integer",
            "description": "Maximum lines to read (default: 100)",
            "nullable": True
        }
    }
    output_type = "string"

    def forward(self, file_path: str, max_lines: int = 100) -> str:
        """Read file contents."""
        try:
            path = Path(file_path)
            if not path.exists():
                return f"File not found: {file_path}"

            if not path.is_file():
                return f"Not a file: {file_path}"

            # Read file with line limit
            with open(path, 'r') as f:
                lines = []
                for i, line in enumerate(f):
                    if i >= max_lines:
                        lines.append(f"\n... (truncated after {max_lines} lines)")
                        break
                    lines.append(line)

                content = ''.join(lines)

            return f"Contents of {file_path}:\n\n{content}"
        except Exception as e:
            return f"Error reading file: {e}"


class ListDirectoryTool(Tool):
    """Lists files in a directory."""

    name = "list_directory"
    description = """
    Lists files and directories in the specified path.

    Use this to explore the working directory and find input files or
    see what outputs are available.

    Input:
    - directory_path: Path to directory (defaults to current directory)
    """
    inputs = {
        "directory_path": {
            "type": "string",
            "description": "Path to directory (default: current directory)",
            "nullable": True
        }
    }
    output_type = "string"

    def forward(self, directory_path: Optional[str] = None) -> str:
        """List directory contents."""
        try:
            path = Path(directory_path or ".")

            if not path.exists():
                return f"Directory not found: {path}"

            if not path.is_dir():
                return f"Not a directory: {path}"

            output = f"Contents of {path.absolute()}:\n\n"

            # Separate directories and files
            dirs = []
            files = []

            for item in sorted(path.iterdir()):
                if item.is_dir():
                    dirs.append(item.name)
                else:
                    files.append(item.name)

            if dirs:
                output += "Directories:\n"
                for d in dirs:
                    output += f"  [DIR]  {d}/\n"
                output += "\n"

            if files:
                output += "Files:\n"
                for f in files:
                    output += f"  [FILE] {f}\n"

            if not dirs and not files:
                output += "(empty directory)\n"

            return output
        except Exception as e:
            return f"Error listing directory: {e}"
