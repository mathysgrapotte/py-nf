import logging
from pathlib import Path

import jpype
import jpype.imports
from dotenv import load_dotenv
from pynf.input_validation import InputValidator
from pynf.runtime_config import (
    assert_nextflow_jar_exists,
    configure_logging,
    resolve_nextflow_jar_path,
)
from pynf.validation import validate_meta_map as _validate_meta_map

# Load environment variables from .env file
load_dotenv()

# Set up logger for this module
logger = logging.getLogger(__name__)

def validate_meta_map(meta: dict, required_fields: list[str] = None):
    """Backwards-compatible facade over the pure validation helper."""
    _validate_meta_map(meta, required_fields)


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
        self._record_task_workdir(event, "onTaskComplete")

    def onTaskCached(self, event):
        self._record_task_workdir(event, "onTaskCached")

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

    # --- Internal helpers ------------------------------------------------------
    def _record_task_workdir(self, event, hook_name):
        logger.debug("%s called", hook_name)
        try:
            handler = event.getHandler()
            task = handler.getTask()
            workdir = str(task.getWorkDir())
            logger.debug("Task workDir: %s", workdir)
            self._task_workdirs.append(workdir)
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.exception("Error getting workDir: %s", exc)


class NextflowEngine:
    def __init__(self, nextflow_jar_path=None):
        jar_path = resolve_nextflow_jar_path(nextflow_jar_path)
        assert_nextflow_jar_exists(jar_path)
        self._start_jvm(jar_path)
        self._load_classes()

    @staticmethod
    def _start_jvm(jar_path: Path):
        """Start the JVM with the Nextflow JAR on the classpath if needed."""
        if not jpype.isJVMStarted():
            jpype.startJVM(classpath=[str(jar_path)])

    def _load_classes(self):
        """Load the Java classes we depend on after the JVM starts."""
        self.ScriptLoaderFactory = jpype.JClass("nextflow.script.ScriptLoaderFactory")
        self.Session = jpype.JClass("nextflow.Session")
        self.Channel = jpype.JClass("nextflow.Channel")
        self.TraceObserverV2 = jpype.JClass("nextflow.trace.TraceObserverV2")
        self.ScriptMeta = jpype.JClass("nextflow.script.ScriptMeta")

    def load_script(self, nf_file_path):
        # Return the Path object for script loading
        return Path(nf_file_path)

    @staticmethod
    def _configure_logging(verbose: bool):
        """Configure Python and (best-effort) Java logging."""
        configure_logging(verbose)

    def execute(
        self,
        script_path,
        executor="local",
        params=None,
        inputs=None,
        config=None,
        docker_config=None,
        verbose=False,
    ):
        """
        Execute a Nextflow script with optional Docker configuration.

        Args:
            script_path: Path to the Nextflow script
            executor: Executor type (default: "local")
            params: Parameters to pass to the script
            inputs: List of dicts, each dict contains parameter names and values for one input channel.
                   Example: [{'meta': {...}, 'input': 'file.bam'}, {'fasta': 'ref.fa'}]
            config: Additional configuration
            docker_config: Docker configuration options:
                - enabled (bool): Enable Docker execution
                - registry (str): Docker registry URL (e.g., 'quay.io' for nf-core modules)
                - registryOverride (bool): Force override registry in fully qualified image names
                - remove (bool): Auto-remove container after execution (default: True)
                - runOptions (str): Additional docker run options
            verbose: Enable verbose debug output (default: False)
        """
        self._configure_logging(verbose)

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

        # Parse and load the script
        loader = self.ScriptLoaderFactory.create(session)
        java_path = jpype.java.nio.file.Paths.get(str(script_path))
        loader.parse(java_path)
        script = loader.getScript()

        # Extract input channels using Nextflow native API
        input_channels = self._get_process_inputs(loader, script)
        logger.debug(f"Discovered input channels: {input_channels}")

        # Validate and map inputs to session.params
        if inputs:
            # Validate inputs against expected structure
            InputValidator.validate_inputs(inputs, input_channels)
            logger.debug(f"Validation passed, setting params for {len(inputs)} input groups")
            self._set_params_from_inputs(session, input_channels, inputs)
            logger.debug(f"Session params after setting: {dict(session.getParams())}")

        collector = _WorkflowOutputCollector()
        observer_proxy = jpype.JProxy(self.TraceObserverV2, inst=collector)
        observer_registered = self._register_output_observer(session, observer_proxy)
        logger.debug(f"Observer registered: {observer_registered}")

        # Execute the script
        try:
            loader.runScript()
            session.fireDataflowNetwork(False)
            session.await_()
            logger.debug(f"After await, collected {len(collector.task_workdirs())} workdirs")
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

        # Optional: set docker registry (e.g., 'quay.io' for nf-core modules)
        if "registry" in docker_config:
            docker_map.put("registry", docker_config["registry"])

        # Optional: set registry override behavior
        if "registryOverride" in docker_config:
            docker_map.put("registryOverride", docker_config["registryOverride"])

        # Optional: set docker run options
        if "runOptions" in docker_config:
            docker_map.put("runOptions", docker_config["runOptions"])

        # Optional: set auto-remove
        if "remove" in docker_config:
            docker_map.put("remove", docker_config["remove"])

    def _extract_tuple_components(self, inp):
        """Extract components from a tuple input parameter."""
        inner = inp.getInner()
        return [
            {"type": str(component.getTypeName()), "name": str(component.getName())}
            for component in inner
        ]

    def _extract_simple_param(self, inp):
        """Extract a simple (non-tuple) input parameter."""
        return {"type": str(inp.getTypeName()), "name": str(inp.getName())}

    def _build_channel_info(self, inp):
        """Build channel info dict from an input parameter."""
        channel_info = {"type": str(inp.getTypeName()), "params": []}

        # Handle tuple inputs
        if hasattr(inp, 'getInner') and inp.getInner() is not None:
            channel_info['params'] = self._extract_tuple_components(inp)
        else:
            # Simple input (val, path, etc.)
            channel_info['params'].append(self._extract_simple_param(inp))

        return channel_info

    def _extract_process_inputs(self, process_def):
        """Extract all inputs from a process definition."""
        process_config = process_def.getProcessConfig()
        inputs = process_config.getInputs()
        return [self._build_channel_info(inp) for inp in inputs]

    def _get_process_inputs(self, loader, script):
        """
        Extract process inputs using Nextflow's native API.

        This replaces the heuristic-based AST parsing approach with
        Nextflow's official process metadata API.

        Args:
            loader: ScriptLoader instance (after parse() has been called)
            script: Script object returned by loader.getScript()

        Returns:
            List of input channel definitions:
            [{'type': str, 'params': [{'type': str, 'name': str}]}]
        """
        try:
            # Set as module to avoid workflow execution
            loader.setModule(True)

            # Run script to register process definitions
            # May fail due to missing params, but processes are registered
            try:
                loader.runScript()
            except Exception:
                pass  # Expected - processes are already registered

            # Get script metadata and process names
            script_meta = self.ScriptMeta.get(script)
            process_names = script_meta.getProcessNames()

            if not process_names or len(process_names) == 0:
                logger.debug("No processes found in script")
                return []

            # Extract inputs from all processes
            # Most nf-core modules have only one process
            all_inputs = []
            for process_name in process_names:
                process_def = script_meta.getProcess(process_name)
                inputs = self._extract_process_inputs(process_def)
                all_inputs.extend(inputs)

            return all_inputs

        except Exception as e:
            logger.exception(f"Error extracting inputs from native API: {e}")
            return []

    def _set_params_from_inputs(self, session, input_channels, inputs):
        """
        Map user inputs to session.params using discovered input channels.

        Args:
            session: Nextflow session
            input_channels: List of expected input channel structures from .nf script
            inputs: List of dicts, each dict contains parameter names and values for one input channel
        """
        params_obj = session.getParams()

        if not input_channels or not inputs:
            return

        # Iterate through each input group and set parameters
        for input_dict, channel_info in zip(inputs, input_channels):
            channel_params = channel_info.get('params', [])

            # For each parameter in this channel, set its value in session.params
            for param_info in channel_params:
                param_name = param_info['name']
                param_type = param_info['type']

                if param_name not in input_dict:
                    continue

                param_value = input_dict[param_name]

                # Convert Python value to appropriate Java type
                java_value = self._convert_to_java_type(param_value, param_type)
                params_obj.put(param_name, java_value)

    def _convert_to_java_type(self, value, param_type):
        """
        Convert Python value to appropriate Java type based on parameter type.

        Args:
            value: Python value to convert
            param_type: Parameter type (val, path, etc.)

        Returns:
            Java object suitable for Nextflow
        """
        HashMap = jpype.JClass("java.util.HashMap")

        # Handle None
        if value is None:
            return None

        # Handle dict (meta maps)
        if isinstance(value, dict):
            meta_map = HashMap()
            for key, val in value.items():
                meta_map.put(key, val)
            return meta_map

        # Handle lists (multiple files, etc.)
        if isinstance(value, list):
            # Convert to comma-separated string for file paths
            return ",".join(str(v) for v in value)

        # For path types, convert to string
        if param_type == 'path':
            return str(value)

        # For val types, return as-is (let JPype handle conversion)
        return value

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
