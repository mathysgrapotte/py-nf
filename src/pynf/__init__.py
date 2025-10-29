from .engine import NextflowEngine, validate_meta_map
from .result import NextflowResult
from .nfcore import (
    download_nfcore_module,
    NFCoreModule,
    NFCoreModuleManager
)

__all__ = [
    'NextflowEngine',
    'NextflowResult',
    'run_module',
    'read_output_file',
    'download_nfcore_module',
    'NFCoreModule',
    'NFCoreModuleManager',
    'validate_meta_map',
]

def run_module(nf_file, inputs=None, params=None, executor="local", docker_config=None, verbose=False):
    """
    Simple one-liner module execution.

    Args:
        nf_file: Path to Nextflow script
        inputs: List of dicts, each dict contains parameter names and values for one input channel
               Example: [{'meta': {...}, 'input': 'file.bam'}, {'fasta': 'ref.fa'}]
        params: Parameters to pass to the script
        executor: Executor type (default: "local")
        docker_config: Docker configuration dict
        verbose: Enable verbose debug output (default: False)

    Returns:
        NextflowResult object
    """
    engine = NextflowEngine()
    script_path = engine.load_script(nf_file)
    return engine.execute(
        script_path,
        executor=executor,
        params=params,
        inputs=inputs,
        docker_config=docker_config,
        verbose=verbose
    )

def read_output_file(file_path):
    """Read contents of an output file"""
    try:
        with open(file_path, 'r') as f:
            return f.read()
    except Exception:
        return None