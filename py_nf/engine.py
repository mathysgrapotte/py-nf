import jpype
import jpype.imports
from pathlib import Path

class NextflowEngine:
    def __init__(self, nextflow_jar_path="nextflow/modules/nextflow/build/libs/nextflow-25.08.0-edge-one.jar"):
        # Start JVM with Nextflow classpath
        if not jpype.isJVMStarted():
            jpype.startJVM(classpath=[nextflow_jar_path])

        # Import Nextflow classes after JVM is started
        self.ScriptRunner = jpype.JClass("nextflow.script.ScriptRunner")
        self.Session = jpype.JClass("nextflow.Session")
        self.Channel = jpype.JClass("nextflow.Channel")

    def load_script(self, nf_file_path):
        # Return the Path object for setScript
        return Path(nf_file_path)

    def execute(self, script_path, executor="local", params=None, input_files=None, config=None):
        # Create session with config
        session = self.Session()

        # Set parameters if provided
        if params:
            for key, value in params.items():
                session.getBinding().setVariable(key, value)

        # Create input channels if files provided
        if input_files:
            input_channel = self.Channel.of(*input_files)
            session.getBinding().setVariable("input", input_channel)

        # Execute script using Java Path
        runner = self.ScriptRunner(session)
        java_path = jpype.java.nio.file.Paths.get(str(script_path))
        runner.setScript(java_path)
        result = runner.execute()

        from .result import NextflowResult
        return NextflowResult(result, session)