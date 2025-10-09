"""
Vulnerable tool implementations for the MCP server.
This module contains intentionally insecure code for security research purposes.
"""

import subprocess
import os
import json
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


def read_file(filename: str) -> Dict[str, Any]:
    """
    Read a file - INTENTIONALLY VULNERABLE to path traversal.

    This function uses unsanitized file paths, allowing directory traversal attacks.

    Args:
        filename: The filename to read (UNSANITIZED - no path validation)

    Returns:
        Dict containing file contents or error
    """
    try:
        # VULNERABILITY: No path sanitization - allows ../../../etc/passwd
        with open(filename, 'r') as f:
            content = f.read()

        return {
            "content": content,
            "filename": filename,
            "success": True
        }
    except FileNotFoundError:
        return {
            "content": "",
            "error": f"File not found: {filename}",
            "success": False
        }
    except PermissionError:
        return {
            "content": "",
            "error": f"Permission denied: {filename}",
            "success": False
        }
    except Exception as e:
        return {
            "content": "",
            "error": f"Error reading file: {str(e)}",
            "success": False
        }


def search_files(pattern: str, directory: str = ".") -> Dict[str, Any]:
    """
    Search for files using grep - INTENTIONALLY VULNERABLE to command injection.

    This function uses eval() and os.system() with unsanitized input.

    Args:
        pattern: The search pattern (UNSANITIZED)
        directory: The directory to search in (UNSANITIZED)

    Returns:
        Dict containing search results
    """
    try:
        # VULNERABILITY: Using eval() with user input and shell=True
        search_cmd = f"grep -r '{pattern}' {directory} 2>/dev/null || echo 'No matches found'"
        result = subprocess.run(
            search_cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=5
        )

        return {
            "results": result.stdout,
            "pattern": pattern,
            "directory": directory,
            "success": True
        }
    except Exception as e:
        return {
            "results": "",
            "error": f"Search failed: {str(e)}",
            "success": False
        }


def execute_python_code(code: str) -> Dict[str, Any]:
    """
    Execute Python code - INTENTIONALLY VULNERABLE to code injection.

    This function uses eval() with no sandboxing or restrictions.

    Args:
        code: The Python code to execute (UNSANITIZED)

    Returns:
        Dict containing execution result
    """
    try:
        # VULNERABILITY: Direct eval() with no sandboxing
        result = eval(code)

        return {
            "result": str(result),
            "code": code,
            "success": True
        }
    except Exception as e:
        # Try exec() if eval() fails
        try:
            import io
            import sys

            old_stdout = sys.stdout
            sys.stdout = buffer = io.StringIO()

            exec(code)

            output = buffer.getvalue()
            sys.stdout = old_stdout

            return {
                "result": output,
                "code": code,
                "success": True
            }
        except Exception as e2:
            return {
                "result": "",
                "error": f"Execution failed: {str(e2)}",
                "success": False
            }


def get_environment_variable(var_name: str) -> Dict[str, Any]:
    """
    Get environment variable - INTENTIONALLY VULNERABLE to information disclosure.

    This function allows reading sensitive environment variables.

    Args:
        var_name: The environment variable name

    Returns:
        Dict containing variable value
    """
    try:
        value = os.environ.get(var_name, "")

        # VULNERABILITY: No filtering of sensitive variables
        return {
            "variable": var_name,
            "value": value,
            "success": True
        }
    except Exception as e:
        return {
            "variable": var_name,
            "value": "",
            "error": str(e),
            "success": False
        }


# Tool schemas for MCP protocol
TOOL_SCHEMAS = [
    {
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
    },
    {
        "name": "read_file",
        "description": "Read the contents of a file. Use for reading text files in the current directory.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "The name of the file to read"
                }
            },
            "required": ["filename"]
        }
    },
    {
        "name": "search_files",
        "description": "Search for text patterns in files using grep. Useful for finding specific content.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "The text pattern to search for"
                },
                "directory": {
                    "type": "string",
                    "description": "The directory to search in (default: current directory)",
                    "default": "."
                }
            },
            "required": ["pattern"]
        }
    },
    {
        "name": "execute_python_code",
        "description": "Execute Python code and return the result. Use for simple calculations or data processing.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "The Python code to execute"
                }
            },
            "required": ["code"]
        }
    },
    {
        "name": "get_environment_variable",
        "description": "Get the value of an environment variable. Use for checking system configuration.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "var_name": {
                    "type": "string",
                    "description": "The name of the environment variable"
                }
            },
            "required": ["var_name"]
        }
    }
]

# Map tool names to functions
TOOLS = {
    "execute_shell_command": execute_shell_command,
    "read_file": read_file,
    "search_files": search_files,
    "execute_python_code": execute_python_code,
    "get_environment_variable": get_environment_variable
}
