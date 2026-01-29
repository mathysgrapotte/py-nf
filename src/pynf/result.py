"""Result object returned from Nextflow execution."""

from collections.abc import Iterable
from functools import lru_cache
from pathlib import Path as _PyPath
from typing import Any, cast

import jpype

from . import outputs as _outputs


@lru_cache(None)
def _java_class(name):
    """Load a Java class via JPype, cached by name."""
    return jpype.JClass(name)


class NextflowResult:
    """Wrap a Nextflow session and its captured outputs.

    Attributes:
        script: Parsed Nextflow script object.
        session: Nextflow session instance.
        loader: Script loader instance.
    """

    def __init__(
        self,
        script,
        session,
        loader,
        workflow_events=None,
        file_events=None,
        task_workdirs=None,
    ):
        self.script = script
        self.session = session
        self.loader = loader
        self._workflow_events = workflow_events or []
        self._file_events = file_events or []
        self._task_workdirs = task_workdirs or []

    def get_output_files(self):
        """Return output file paths, preferring published metadata.

        Returns:
            Ordered list of unique output file paths.
        """
        paths = self._collect_paths_from_observer()
        if not paths:
            paths = self._collect_paths_from_workdir()
        return paths

    def _collect_paths_from_observer(self):
        """Collect output paths from workflow observer events."""
        return _outputs.collect_paths_from_events(
            self._workflow_events, self._file_events
        )

    def _collect_paths_from_workdir(self):
        """Collect output paths by scanning task work directories."""
        return _outputs.collect_paths_from_workdirs(self._task_workdirs)

    def get_workflow_outputs(self):
        """Return structured representation of workflow outputs.

        Returns:
            List of workflow output dictionaries with ``name`` and ``value``.
        """

        def convert(value):
            if value is None:
                return None
            if isinstance(value, (str, int, float, bool)):
                return value
            if isinstance(value, _PyPath):
                return str(value)
            if isinstance(value, (list, tuple, set)):
                return [convert(item) for item in value]
            if isinstance(value, dict):
                return {convert(k): convert(v) for k, v in value.items()}
            if hasattr(value, "entrySet") and callable(value.entrySet):
                result = {}
                entry_set = value.entrySet()
                iterator_factory = getattr(entry_set, "iterator", None)
                if callable(iterator_factory):
                    iterator = iterator_factory()
                    while iterator.hasNext():  # type: ignore[attr-defined]
                        entry = iterator.next()  # type: ignore[attr-defined]
                        result[convert(entry.getKey())] = convert(entry.getValue())
                return result
            if isinstance(value, Iterable):
                return [convert(item) for item in cast(Iterable[Any], value)]
            iterator_factory = getattr(value, "iterator", None)
            if callable(iterator_factory):
                iterator = iterator_factory()
                collected = []
                while iterator.hasNext():  # type: ignore[attr-defined]
                    collected.append(convert(iterator.next()))  # type: ignore[attr-defined]
                return collected
            return str(value)

        outputs = []
        for event in self._workflow_events:
            if not isinstance(event, dict):
                continue
            outputs.append(
                {
                    "name": event.get("name"),
                    "value": convert(event.get("value")),
                    "index": convert(event.get("index")),
                }
            )
        return outputs

    def get_process_outputs(self):
        """Return process output metadata using Nextflow infrastructure.

        Returns:
            Mapping of process names to output metadata.
        """
        ScriptMeta = jpype.JClass("nextflow.script.ScriptMeta")
        script_meta = ScriptMeta.get(self.script)

        outputs = {}
        for process_name in list(script_meta.getLocalProcessNames()):
            process_def = script_meta.getProcess(process_name)
            process_config = process_def.getProcessConfig()
            declared_outputs = process_config.getOutputs()
            outputs[process_name] = {
                "output_count": declared_outputs.size(),
                "output_names": [str(out.getName()) for out in declared_outputs],
            }
        return outputs

    def get_stdout(self):
        """Return the first available process stdout.

        Returns:
            Stdout contents when available, otherwise an empty string.
        """
        Files = _java_class("java.nio.file.Files")
        work_dir = self.session.getWorkDir().toFile()
        for hash_prefix in work_dir.listFiles():
            for task_dir in hash_prefix.listFiles():
                stdout_path = task_dir.toPath().resolve(".command.out")
                return str(Files.readString(stdout_path))
        return ""

    def get_execution_report(self):
        """Return execution statistics from the Nextflow session.

        Returns:
            Mapping containing task counts and the work directory.
        """
        stats = self.session.getStatsObserver().getStats()
        return {
            "completed_tasks": stats.getSucceededCount(),
            "failed_tasks": stats.getFailedCount(),
            "work_dir": str(self.session.getWorkDir()),
        }
