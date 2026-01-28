from functools import lru_cache
from pathlib import Path as _PyPath

import jpype

from . import outputs as _outputs


@lru_cache(None)
def _java_class(name):
    return jpype.JClass(name)


class NextflowResult:
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
        """Get output file paths, preferring published metadata when available."""
        paths = self._collect_paths_from_observer()
        if not paths:
            paths = self._collect_paths_from_workdir()
        return paths

    def _collect_paths_from_observer(self):
        return _outputs.collect_paths_from_events(self._workflow_events, self._file_events)

    @staticmethod
    def _extend_unique(result_list, seen, values):
        """Append unseen values to result_list while preserving order."""
        for value in values:
            if value not in seen:
                seen.add(value)
                result_list.append(value)

    def _flatten_paths(self, value):
        """Yield string paths extracted from nested Java/Python structures."""
        yield from _outputs.flatten_paths(value)

    def _collect_paths_from_workdir(self):
        """Fallback to work directory traversal (only scans tracked task workDirs)."""
        return _outputs.collect_paths_from_workdirs(self._task_workdirs)

    def get_workflow_outputs(self):
        """Return structured representation of workflow outputs."""

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
            if jpype.isJArray(value):
                return [convert(item) for item in value]
            if hasattr(value, "entrySet") and callable(value.entrySet):
                result = {}
                for entry in value.entrySet():
                    result[convert(entry.getKey())] = convert(entry.getValue())
                return result
            try:
                return [convert(item) for item in value]
            except TypeError:
                if hasattr(value, "iterator"):
                    iterator = value.iterator()
                    collected = []
                    while iterator.hasNext():
                        collected.append(convert(iterator.next()))
                    return collected
                pass
            try:
                return str(value)
            except Exception:
                return value

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
        """Get process output metadata using Nextflow's infrastructure"""
        import jpype
        ScriptMeta = jpype.JClass("nextflow.script.ScriptMeta")
        script_meta = ScriptMeta.get(self.script)

        outputs = {}
        for process_name in list(script_meta.getLocalProcessNames()):
            process_def = script_meta.getProcess(process_name)
            process_config = process_def.getProcessConfig()
            declared_outputs = process_config.getOutputs()
            outputs[process_name] = {
                'output_count': declared_outputs.size(),
                'output_names': [str(out.getName()) for out in declared_outputs]
            }
        return outputs

    def get_stdout(self):
        """Get stdout from processes"""
        Files = _java_class("java.nio.file.Files")
        work_dir = self.session.getWorkDir().toFile()
        for hash_prefix in work_dir.listFiles():
            for task_dir in hash_prefix.listFiles():
                stdout_path = task_dir.toPath().resolve(".command.out")
                return str(Files.readString(stdout_path))
        return ""

    def get_execution_report(self):
        """Get execution statistics"""
        stats = self.session.getStatsObserver().getStats()
        return {
            'completed_tasks': stats.getSucceededCount(),
            'failed_tasks': stats.getFailedCount(),
            'work_dir': str(self.session.getWorkDir())
        }
