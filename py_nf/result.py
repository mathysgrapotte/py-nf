class NextflowResult:
    def __init__(self, groovy_result, session):
        self.result = groovy_result
        self.session = session

    def get_output_files(self):
        """Extract output file paths from Nextflow execution"""
        outputs = []
        try:
            # Navigate through session work directory
            work_dir = self.session.getWorkDir()
            if work_dir and work_dir.exists():
                # Collect all output files from completed tasks
                for task_dir in work_dir.listFiles():
                    if task_dir.isDirectory():
                        for file in task_dir.listFiles():
                            if file.isFile():
                                outputs.append(str(file.getAbsolutePath()))
        except Exception as e:
            # If there's an error accessing files, return empty list
            pass
        return outputs

    def get_stdout(self):
        """Get stdout from processes"""
        try:
            if hasattr(self.result, 'getStdout'):
                return str(self.result.getStdout())
            return ""
        except Exception:
            return ""

    def get_execution_report(self):
        """Get execution statistics"""
        try:
            return {
                'completed_tasks': self.session.getCompletedCount() if hasattr(self.session, 'getCompletedCount') else 0,
                'failed_tasks': self.session.getFailedCount() if hasattr(self.session, 'getFailedCount') else 0,
                'work_dir': str(self.session.getWorkDir()) if hasattr(self.session, 'getWorkDir') else ""
            }
        except Exception:
            return {
                'completed_tasks': 0,
                'failed_tasks': 0,
                'work_dir': ""
            }