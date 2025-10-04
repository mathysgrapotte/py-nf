from .engine import NextflowEngine
from .result import NextflowResult

__all__ = ['NextflowEngine', 'NextflowResult']

def run_workflow(nf_file, input_files=None, params=None, executor="local"):
    """Simple one-liner workflow execution"""
    engine = NextflowEngine()
    script_path = engine.load_script(nf_file)
    return engine.execute(script_path, executor=executor, params=params, input_files=input_files)