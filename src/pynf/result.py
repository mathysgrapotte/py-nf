from functools import lru_cache
from pathlib import Path as _PyPath

import jpype


@lru_cache(None)
def _java_class(name):
    return jpype.JClass(name)


class NextflowResult:
    def __init__(self, script, session, loader, workflow_events=None, file_events=None, task_workdirs=None):
        self.script = script
        self.session = session
        self.loader = loader
        self._workflow_events = workflow_events or []
        self._file_events = file_events or []
        self._task_workdirs = task_workdirs or []

    def get_output_files(self):
        """Get output file paths, preferring published metadata when available."""
        paths = self._collect_paths_from_observer()

        # DEBUG
        print(f"DEBUG: Observer paths: {paths}")
        print(f"DEBUG: task_workdirs: {self._task_workdirs}")

        if not paths:
            paths = self._collect_paths_from_workdir()
            print(f"DEBUG: Workdir scan paths: {paths}")

        return paths

    def _collect_paths_from_observer(self):
        seen = set()
        result = []

        for event in self._workflow_events:
            value = event.get("value") if isinstance(event, dict) else None
            if value is not None:
                for path_str in self._flatten_paths(value):
                    if path_str not in seen:
                        seen.add(path_str)
                        result.append(path_str)

            index = event.get("index") if isinstance(event, dict) else None
            if index is not None:
                for path_str in self._flatten_paths(index):
                    if path_str not in seen:
                        seen.add(path_str)
                        result.append(path_str)

        for event in self._file_events:
            target = event.get("target") if isinstance(event, dict) else None
            if target is None:
                continue
            for path_str in self._flatten_paths(target):
                if path_str not in seen:
                    seen.add(path_str)
                    result.append(path_str)

        return result

    def _flatten_paths(self, value):
        """Yield string paths extracted from nested Java/Python structures."""

        def visit(obj):
            if obj is None:
                return

            # Avoid treating strings as iterables of characters
            if isinstance(obj, str):
                if obj:
                    yield obj
                return

            # java.nio.file.Path or java.io.File
            try:
                java_path = _java_class("java.nio.file.Path")
                if isinstance(obj, java_path):
                    yield str(obj.toAbsolutePath())
                    return
            except RuntimeError:
                pass

            try:
                java_file = _java_class("java.io.File")
                if isinstance(obj, java_file):
                    yield str(obj.toPath())
                    return
            except RuntimeError:
                pass

            # Pathlib paths
            if isinstance(obj, _PyPath):
                yield str(obj)
                return

            # Python collections
            if isinstance(obj, (list, tuple, set)):
                for item in obj:
                    yield from visit(item)
                return

            if isinstance(obj, dict):
                for item in obj.values():
                    yield from visit(item)
                return

            # Java arrays
            if jpype.isJArray(obj):
                for item in obj:
                    yield from visit(item)
                return

            if hasattr(obj, "entrySet") and callable(obj.entrySet):
                for entry in obj.entrySet():
                    yield from visit(entry.getValue())
                return

            # Java collections / iterables
            if hasattr(obj, "iterator"):
                iterator = obj.iterator()
                while iterator.hasNext():
                    yield from visit(iterator.next())
                return

            try:
                for item in obj:
                    yield from visit(item)
                return
            except TypeError:
                pass

            # Map entries (java.util.Map$Entry)
            if hasattr(obj, "getValue") and callable(obj.getValue):
                yield from visit(obj.getValue())
                return

        yield from visit(value)

    def _collect_paths_from_workdir(self):
        """Fallback to work directory traversal (only scans tracked task workDirs)."""
        from pathlib import Path as _PyPath

        outputs = []
        print(f"DEBUG: Scanning {len(self._task_workdirs)} workdirs")

        # Use tracked workDirs from current run if available
        for workdir_str in self._task_workdirs:
            workdir = _PyPath(workdir_str)
            print(f"DEBUG: Scanning workdir: {workdir}")
            print(f"DEBUG: Workdir exists: {workdir.exists()}")

            if workdir.exists():
                files = list(workdir.iterdir())
                print(f"DEBUG: Files in workdir: {files}")

            for file in workdir.iterdir():
                if file.is_file() and not file.name.startswith('.'):
                    path_str = str(file.absolute())
                    if path_str not in outputs:
                        outputs.append(path_str)

        return outputs

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