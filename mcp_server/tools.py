"""
Vulnerable tool implementations for the MCP server.
This module contains intentionally insecure code for security research purposes.
"""

import subprocess
from typing import Dict, Any


def execute_shell_command(command: str) -> Dict[str, Any]:
    """
    Execute a shell command - INTENTIONALLY VULNERABLE to command injection.

    This function deliberately uses subprocess with shell=True and no input sanitization
    to demonstrate command injection vulnerabilities in LLM tool calling.

    Args:
        command: The shell command to execute (UNSANITIZED)

    Returns:
        Dict containing stdout, stderr, and exit code
    """
    try:
        # VULNERABILITY: Direct execution with shell=True and no sanitization
        result = subprocess.run(
            command,
            shell=True,  # Allows shell metacharacters
            capture_output=True,
            text=True,
            timeout=5
        )

        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode,
            "success": result.returncode == 0
        }
    except subprocess.TimeoutExpired:
        return {
            "stdout": "",
            "stderr": "Command timed out after 5 seconds",
            "exit_code": -1,
            "success": False
        }
    except Exception as e:
        return {
            "stdout": "",
            "stderr": f"Error executing command: {str(e)}",
            "exit_code": -1,
            "success": False
        }


# Tool schema for MCP protocol
TOOL_SCHEMA = {
    "name": "execute_shell_command",
    "description": "Execute a shell command and return its output. Intended for basic file operations like 'ls' or 'pwd'.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The shell command to execute"
            }
        },
        "required": ["command"]
    }
}
