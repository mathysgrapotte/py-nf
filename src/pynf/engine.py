import os
import jpype
import jpype.imports
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def validate_meta_map(meta: dict, required_fields: list[str] = None):
    """
    Validate meta map contains required fields.

    Args:
        meta: Meta map dictionary
        required_fields: List of required field names

    Raises:
        ValueError: If required fields are missing

    Example:
        >>> validate_meta_map({'id': 'sample1'}, required_fields=['id'])
        >>> validate_meta_map({'name': 'test'}, required_fields=['id'])
        ValueError: Missing required meta field: id
    """
    if required_fields is None:
        required_fields = ['id']  # 'id' is always required

    missing_fields = [field for field in required_fields if field not in meta]

    if missing_fields:
        raise ValueError(
            f"Missing required meta fields: {', '.join(missing_fields)}. "
            f"Meta map provided: {meta}"
        )


class _WorkflowOutputCollector:
    """Bridge TraceObserverV2 callbacks into Python structures."""

    def __init__(self):
        self._workflow_events = []
        self._file_events = []
        self._task_workdirs = []

    # --- TraceObserverV2 hooks (no-ops unless otherwise noted) ---
    def onFlowCreate(self, session):  # noqa: D401 - required signature
        return None

    def onFlowBegin(self):
        return None

    def onFlowComplete(self):
        return None

    def onProcessCreate(self, process):
        return None

    def onProcessTerminate(self, process):
        return None

    def onTaskPending(self, event):
        return None

    def onTaskSubmit(self, event):
        return None

    def onTaskStart(self, event):
        return None

    def onTaskComplete(self, event):
        print(f"DEBUG: onTaskComplete called")
        try:
            # Use getHandler() method instead of .handler attribute
            handler = event.getHandler()
            task = handler.getTask()
            workdir = str(task.getWorkDir())
            print(f"DEBUG: Task workDir: {workdir}")
            self._task_workdirs.append(workdir)
        except Exception as e:
            print(f"DEBUG: Error getting workDir: {e}")
            import traceback
            traceback.print_exc()

    def onTaskCached(self, event):
        print(f"DEBUG: onTaskCached called")
        try:
            # Use getHandler() method instead of .handler attribute
            handler = event.getHandler()
            task = handler.getTask()
            workdir = str(task.getWorkDir())
            print(f"DEBUG: Task workDir: {workdir}")
            self._task_workdirs.append(workdir)
        except Exception as e:
            print(f"DEBUG: Error getting workDir: {e}")
            import traceback
            traceback.print_exc()

    def onFlowError(self, event):
        return None

    def onWorkflowOutput(self, event):  # pragma: no cover - JVM callback
        self._workflow_events.append(
            {
                "name": event.getName(),
                "value": event.getValue(),
                "index": event.getIndex(),
            }
        )

    def onFilePublish(self, event):  # pragma: no cover - JVM callback
        self._file_events.append(
            {
                "target": event.getTarget(),
                "source": event.getSource(),
                "labels": event.getLabels(),
            }
        )

    # --- Convenience accessors -------------------------------------------------
    def workflow_events(self):
        return list(self._workflow_events)

    def file_events(self):
        return list(self._file_events)

    def task_workdirs(self):
        return list(self._task_workdirs)


class NextflowEngine:
    def __init__(self, nextflow_jar_path=None):
        # Use provided path, or environment variable, or default
        if nextflow_jar_path is None:
            nextflow_jar_path = os.getenv(
                "NEXTFLOW_JAR_PATH",
                "nextflow/build/releases/nextflow-25.10.0-one.jar"
            )

        # Check if JAR file exists
        jar_path = Path(nextflow_jar_path)
        if not jar_path.exists():
            error_msg = (
                f"\n{'='*70}\n"
                f"ERROR: Nextflow JAR not found at: {nextflow_jar_path}\n"
                f"{'='*70}\n\n"
                f"This project requires a Nextflow fat JAR to run.\n\n"
                f"To set up Nextflow automatically, run:\n"
                f"    python setup_nextflow.py\n\n"
                f"This will clone and build Nextflow for you.\n\n"
                f"Alternatively, you can set up manually:\n"
                f"1. Clone: git clone https://github.com/nextflow-io/nextflow.git\n"
                f"2. Build: cd nextflow && make pack\n"
                f"3. Update .env with the JAR path\n"
                f"{'='*70}\n"
            )
            raise FileNotFoundError(error_msg)

        # Start JVM with Nextflow classpath
        if not jpype.isJVMStarted():
            jpype.startJVM(classpath=[nextflow_jar_path])

        # Import Nextflow classes after JVM is started
        self.ScriptLoaderFactory = jpype.JClass("nextflow.script.ScriptLoaderFactory")
        self.Session = jpype.JClass("nextflow.Session")
        self.Channel = jpype.JClass("nextflow.Channel")
        self.TraceObserverV2 = jpype.JClass("nextflow.trace.TraceObserverV2")

    def load_script(self, nf_file_path):
        # Return the Path object for script loading
        return Path(nf_file_path)

    def execute(self, script_path, executor="local", params=None, input_files=None, config=None, docker_config=None, meta=None):
        """
        Execute a Nextflow script with optional Docker configuration.

        Args:
            script_path: Path to the Nextflow script
            executor: Executor type (default: "local")
            params: Parameters to pass to the script
            input_files: Input files for the script
            config: Additional configuration
            docker_config: Docker configuration options:
                - enabled (bool): Enable Docker execution
                - remove (bool): Auto-remove container after execution (default: True)
                - runOptions (str): Additional docker run options
            meta: Metadata map for nf-core modules (e.g., {'id': 'sample1', 'single_end': False})
        """
        # Create session with config
        session = self.Session()

        # Apply Docker configuration if provided
        if docker_config:
            self._configure_docker(session, docker_config)

        # Initialize session with script file
        ArrayList = jpype.JClass("java.util.ArrayList")
        ScriptFile = jpype.JClass("nextflow.script.ScriptFile")
        script_file = ScriptFile(jpype.java.nio.file.Paths.get(str(script_path)))
        session.init(script_file, ArrayList(), None, None)
        session.start()

        # Set parameters if provided
        if params:
            for key, value in params.items():
                session.getBinding().setVariable(key, value)

        # Create input channels if files provided
        if meta and input_files:
            # Handle meta map + input files for nf-core modules
            input_channel = self._create_meta_channel(session, meta, input_files)
            session.getBinding().setVariable("input", input_channel)
        elif input_files:
            # Legacy behavior: just files without meta
            input_channel = self.Channel.of(*input_files)
            session.getBinding().setVariable("input", input_channel)

        # Parse the script with the v2 loader (DSL2 syntax)
        loader = self.ScriptLoaderFactory.create(session)
        java_path = jpype.java.nio.file.Paths.get(str(script_path))
        loader.parse(java_path)

        collector = _WorkflowOutputCollector()
        observer_proxy = jpype.JProxy(self.TraceObserverV2, inst=collector)
        observer_registered = self._register_output_observer(session, observer_proxy)
        print(f"DEBUG: Observer registered: {observer_registered}")

        # Capture script before execution
        script = loader.getScript()
        try:
            loader.runScript()
            session.fireDataflowNetwork(False)
            session.await_()
            print(f"DEBUG: After await, collected {len(collector.task_workdirs())} workdirs")
        finally:
            if observer_registered:
                self._unregister_output_observer(session, observer_proxy)
            session.destroy()

        from .result import NextflowResult
        return NextflowResult(
            script,
            session,
            loader,
            workflow_events=collector.workflow_events(),
            file_events=collector.file_events(),
            task_workdirs=collector.task_workdirs(),
        )

    def _configure_docker(self, session, docker_config):
        """
        Configure Docker settings for the Nextflow session.

        This method sets up Docker configuration before the session is initialized,
        allowing container execution.

        Args:
            session: Nextflow session object
            docker_config: Docker configuration dict
        """
        # Import Java HashMap for configuration
        HashMap = jpype.JClass("java.util.HashMap")

        # Get the session config map
        config = session.getConfig()

        # Create or get docker config section
        if not config.containsKey("docker"):
            docker_map = HashMap()
            config.put("docker", docker_map)
        else:
            docker_map = config.get("docker")

        # Set Docker as enabled
        docker_map.put("enabled", docker_config.get("enabled", True))

        # Optional: set docker run options
        if "runOptions" in docker_config:
            docker_map.put("runOptions", docker_config["runOptions"])

        # Optional: set auto-remove
        if "remove" in docker_config:
            docker_map.put("remove", docker_config["remove"])

    def _create_meta_channel(self, session, meta, input_files):
        """
        Create a Nextflow channel with tuple val(meta), path(files).

        This is the standard input format for nf-core modules.

        Args:
            session: Nextflow session
            meta: Python dict with metadata (e.g., {'id': 'sample1'})
            input_files: List of file paths or single file path

        Returns:
            Nextflow channel containing tuple(meta_map, file_paths)
        """
        # Validate meta map
        validate_meta_map(meta)

        # Import Java classes
        HashMap = jpype.JClass("java.util.HashMap")
        ArrayList = jpype.JClass("java.util.ArrayList")

        # Convert Python dict to Java HashMap
        meta_map = HashMap()
        for key, value in meta.items():
            meta_map.put(key, value)

        # Ensure input_files is a list
        if not isinstance(input_files, list):
            input_files = [input_files]

        # Convert file paths to Java Path objects
        file_paths = ArrayList()
        for file_path in input_files:
            java_path = jpype.java.nio.file.Paths.get(str(file_path))
            file_paths.add(java_path)

        # Create a tuple: [meta_map, file_paths]
        # For single file, just use the path directly
        if len(file_paths) == 1:
            tuple_value = ArrayList()
            tuple_value.add(meta_map)
            tuple_value.add(file_paths.get(0))
        else:
            tuple_value = ArrayList()
            tuple_value.add(meta_map)
            tuple_value.add(file_paths)

        # Create channel with this tuple
        channel = self.Channel.of(tuple_value)

        return channel

    # ------------------------------------------------------------------
    def _register_output_observer(self, session, observer):
        try:
            return self._mutate_observers(session, observer, add=True)
        except Exception:
            return False

    def _unregister_output_observer(self, session, observer):
        try:
            self._mutate_observers(session, observer, add=False)
        except Exception:
            pass

    def _mutate_observers(self, session, observer, add=True):
        session_class = session.getClass()
        field = session_class.getDeclaredField("observersV2")
        field.setAccessible(True)
        observers = field.get(session)
        if add:
            observers.add(observer)
        else:
            observers.remove(observer)
        field.set(session, observers)
        return True
