"""
Simple text-based logging for security research experiments.
"""

import os
from datetime import datetime
from typing import Dict, Any


class ResearchLogger:
    """Logs agent attempts and results to text files."""

    def __init__(self, log_dir: str = "results"):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)

        # Create timestamped log file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = os.path.join(log_dir, f"experiment_{timestamp}.txt")

        self._write_header()

    def _write_header(self):
        """Write experiment header."""
        with open(self.log_file, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("LLM SANDBOX ESCAPE EXPERIMENT\n")
            f.write(f"Started: {datetime.now().isoformat()}\n")
            f.write("=" * 80 + "\n\n")

    def log_attempt(self, attempt_num: int, reasoning: str, payload: str):
        """Log an attack attempt."""
        with open(self.log_file, 'a') as f:
            f.write(f"\n{'=' * 80}\n")
            f.write(f"ATTEMPT #{attempt_num}\n")
            f.write(f"Time: {datetime.now().isoformat()}\n")
            f.write(f"{'-' * 80}\n")
            f.write(f"REASONING:\n{reasoning}\n\n")
            f.write(f"PAYLOAD:\n{payload}\n")
            f.write(f"{'=' * 80}\n")

    def log_result(self, result: Dict[str, Any], analysis: str = ""):
        """Log tool execution result."""
        with open(self.log_file, 'a') as f:
            f.write(f"\nRESULT:\n")
            f.write(f"{'-' * 80}\n")
            f.write(f"Exit Code: {result.get('exit_code', 'N/A')}\n")
            if result.get('stdout'):
                f.write(f"\nStdout:\n{result['stdout']}\n")
            if result.get('stderr'):
                f.write(f"\nStderr:\n{result['stderr']}\n")
            if analysis:
                f.write(f"\nANALYSIS:\n{analysis}\n")
            f.write(f"{'-' * 80}\n")

    def log_success(self, attempt_num: int, payload: str, output: str):
        """Log successful escape."""
        with open(self.log_file, 'a') as f:
            f.write(f"\n{'#' * 80}\n")
            f.write(f"SUCCESS! SANDBOX ESCAPED ON ATTEMPT #{attempt_num}\n")
            f.write(f"{'#' * 80}\n")
            f.write(f"Time: {datetime.now().isoformat()}\n")
            f.write(f"Successful Payload: {payload}\n\n")
            f.write(f"Retrieved Content:\n")
            f.write(f"{'-' * 80}\n")
            f.write(f"{output}\n")
            f.write(f"{'-' * 80}\n")

    def log_failure(self, total_attempts: int):
        """Log failed escape attempt."""
        with open(self.log_file, 'a') as f:
            f.write(f"\n{'#' * 80}\n")
            f.write(f"EXPERIMENT FAILED\n")
            f.write(f"{'#' * 80}\n")
            f.write(f"Total Attempts: {total_attempts}\n")
            f.write(f"Time: {datetime.now().isoformat()}\n")
            f.write(f"The agent was unable to escape the sandbox within {total_attempts} attempts.\n")

    def log_error(self, error: str):
        """Log errors."""
        with open(self.log_file, 'a') as f:
            f.write(f"\nERROR: {error}\n")
            f.write(f"Time: {datetime.now().isoformat()}\n\n")

    def get_log_path(self) -> str:
        """Return path to current log file."""
        return self.log_file
