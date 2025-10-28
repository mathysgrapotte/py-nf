from .engine import NextflowEngine
from .result import NextflowResult
from .wave import WaveClient

__all__ = [
    "NextflowEngine",
    "NextflowResult",
    "WaveClient",
    "run_module",
    "read_output_file",
]


def run_module(nf_file, input_files=None, params=None, executor="local"):
    """Simple one-liner module execution"""
    engine = NextflowEngine()
    script_path = engine.load_script(nf_file)
    return engine.execute(
        script_path, executor=executor, params=params, input_files=input_files
    )


def read_output_file(file_path):
    """Read contents of an output file"""
    try:
        with open(file_path, "r") as f:
            return f.read()
    except Exception:
        return None
