class NextflowResult:
    def __init__(self, script, session, loader):
        self.script = script
        self.session = session
        self.loader = loader

    def get_output_files(self):
        """Get output file paths from work directory"""
        work_dir_path = self.session.getWorkDir()
        if not work_dir_path:
            return []
        work_dir = work_dir_path.toFile()
        if not work_dir.exists():
            return []

        # Get declared output patterns from ScriptMeta
        import jpype
        ScriptMeta = jpype.JClass("nextflow.script.ScriptMeta")
        script_meta = ScriptMeta.get(self.script)

        outputs = []

        # Look through task directories to find actual output files
        for task_dir in work_dir.listFiles():
            for subdir in task_dir.listFiles():
                # Check for declared output files (not starting with .)
                for file in subdir.listFiles():
                    if file.isFile() and not file.getName().startsWith('.'):
                        outputs.append(str(file.getAbsolutePath()))

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
        work_dir = self.session.getWorkDir()
        for task_dir in work_dir.listFiles():
            stdout_file = task_dir.toPath().resolve(".command.out")
            return stdout_file.toFile().getText()
        return ""

    def get_execution_report(self):
        """Get execution statistics"""
        return {
            'completed_tasks': self.session.getCompletedCount(),
            'failed_tasks': self.session.getFailedCount(),
            'work_dir': str(self.session.getWorkDir())
        }