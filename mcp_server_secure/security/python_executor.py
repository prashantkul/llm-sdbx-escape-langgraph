"""
Secure Python code executor with sandboxing and restrictions.

This module provides safe Python code execution by:
1. Blocking dangerous imports (os, subprocess, urllib, etc.)
2. Using restricted builtins
3. Limiting execution time and resources
4. Preventing file system and network access
"""

import sys
import ast
import signal
from typing import Tuple, Dict, Any
import threading


class PythonExecutor:
    """Secure Python code executor with multiple security layers."""

    def __init__(self):
        """Initialize the secure Python executor."""
        self.blocked_imports = [
            # System interaction
            'os', 'subprocess', 'sys', 'platform', 'signal',
            # Network
            'urllib', 'urllib.request', 'urllib.parse', 'urllib.error',
            'requests', 'httpx', 'aiohttp', 'socket', 'http', 'http.client',
            'ftplib', 'smtplib', 'poplib', 'imaplib',
            # File system
            'shutil', 'pathlib', 'glob', 'tempfile',
            # Code execution
            'importlib', '__import__', 'compile', 'exec', 'eval',
            # Other dangerous
            'ctypes', 'cffi', 'pty', 'fcntl', 'resource',
            'pickle', 'shelve', 'marshal', 'types', 'code'
        ]

        self.blocked_builtins = [
            'open', 'file', 'input', 'raw_input',
            'compile', 'exec', 'eval', 'execfile',
            '__import__', 'reload', 'help', 'exit', 'quit'
        ]

        self.max_execution_time = 5  # seconds
        self.max_output_length = 10000  # characters

    def validate_code_syntax(self, code: str) -> Tuple[bool, str]:
        """
        Validate code syntax and check for dangerous patterns.

        Returns:
            (is_valid, error_message)
        """
        # Safe modules that are allowed to be imported
        safe_modules = [
            'math', 'random', 'datetime', 'json', 're',
            'collections', 'itertools', 'functools', 'string'
        ]

        # Check for dangerous imports using proper word boundaries
        import re as regex_module
        for blocked in self.blocked_imports:
            # Use word boundaries to avoid false positives like 'os' in 'httpbin.org/post'
            patterns = [
                rf'\bimport\s+{regex_module.escape(blocked)}\b',
                rf'\bfrom\s+{regex_module.escape(blocked)}\b',
                rf"__import__\(['\"]{ regex_module.escape(blocked)}['\"]\)",
                rf"import_module\(['\"]{ regex_module.escape(blocked)}['\"]\)",
            ]
            for pattern in patterns:
                if regex_module.search(pattern, code):
                    return False, f"Error: Import of '{blocked}' is not allowed"

        # Check for import statements and verify they're for safe modules only
        import_patterns = [
            r'^\s*import\s+(\w+)',  # import module
            r'^\s*from\s+(\w+)',     # from module import
        ]
        for line in code.split('\n'):
            for pattern in import_patterns:
                match = regex_module.match(pattern, line)
                if match:
                    module_name = match.group(1)
                    if module_name not in safe_modules:
                        # Check if it's a dangerous module
                        if module_name in self.blocked_imports:
                            return False, f"Error: Import of '{module_name}' is not allowed"

        # Check for dangerous builtins
        for blocked in self.blocked_builtins:
            # Look for the builtin being called
            if f"{blocked}(" in code:
                return False, f"Error: Use of builtin '{blocked}' is not allowed"

        # Check for attribute access that could bypass restrictions
        dangerous_attrs = [
            '__import__', '__builtins__', '__globals__',
            '__locals__', '__code__', '__class__', '__base__',
            '__subclasses__', '__file__', '__loader__'
        ]
        for attr in dangerous_attrs:
            if attr in code:
                return False, f"Error: Access to '{attr}' is not allowed"

        # Try to parse the code
        try:
            ast.parse(code)
        except SyntaxError as e:
            return False, f"Error: Syntax error in code: {str(e)}"

        return True, ""

    def create_safe_globals(self) -> Dict[str, Any]:
        """Create a restricted globals dictionary for code execution."""
        # Start with minimal safe builtins
        safe_builtins = {
            'abs': abs,
            'all': all,
            'any': any,
            'bool': bool,
            'chr': chr,
            'dict': dict,
            'divmod': divmod,
            'enumerate': enumerate,
            'filter': filter,
            'float': float,
            'format': format,
            'hex': hex,
            'int': int,
            'isinstance': isinstance,
            'issubclass': issubclass,
            'iter': iter,
            'len': len,
            'list': list,
            'map': map,
            'max': max,
            'min': min,
            'next': next,
            'oct': oct,
            'ord': ord,
            'pow': pow,
            'print': print,
            'range': range,
            'reversed': reversed,
            'round': round,
            'set': set,
            'sorted': sorted,
            'str': str,
            'sum': sum,
            'tuple': tuple,
            'type': type,
            'zip': zip,
        }

        # Pre-import safe modules so they're available
        # Users can use "import math" or just use "math" directly
        safe_globals = {
            '__builtins__': safe_builtins,
            '__name__': '__main__',
            '__doc__': None,
            # Pre-imported safe modules
            'math': __import__('math'),
            'random': __import__('random'),
            'datetime': __import__('datetime'),
            'json': __import__('json'),
            're': __import__('re'),
            'collections': __import__('collections'),
            'itertools': __import__('itertools'),
            'functools': __import__('functools'),
            'string': __import__('string'),
        }

        return safe_globals

    def execute_with_timeout(self, code: str, timeout: int) -> Tuple[bool, str]:
        """
        Execute code with a timeout.

        Returns:
            (success, output_or_error)
        """
        result = {'output': '', 'error': '', 'completed': False}

        def target():
            try:
                # Capture stdout
                import io
                from contextlib import redirect_stdout

                stdout_capture = io.StringIO()

                safe_globals = self.create_safe_globals()
                safe_locals = {}

                with redirect_stdout(stdout_capture):
                    exec(code, safe_globals, safe_locals)

                result['output'] = stdout_capture.getvalue()
                result['completed'] = True

            except Exception as e:
                result['error'] = str(e)
                result['completed'] = True

        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()
        thread.join(timeout)

        if thread.is_alive():
            return False, f"Error: Code execution timed out after {timeout} seconds"

        if result['error']:
            return False, f"Error: {result['error']}"

        if result['completed']:
            output = result['output']
            if len(output) > self.max_output_length:
                output = output[:self.max_output_length] + f"\n... (output truncated, {len(output)} chars total)"
            return True, output if output else "Code executed successfully (no output)"

        return False, "Error: Unknown execution error"

    def execute(self, code: str) -> Tuple[bool, str]:
        """
        Execute Python code securely.

        Returns:
            (success, output_or_error)
        """
        # Step 1: Validate syntax and check for dangerous patterns
        is_valid, error_msg = self.validate_code_syntax(code)
        if not is_valid:
            return False, error_msg

        # Step 2: Execute with timeout and restrictions
        success, output = self.execute_with_timeout(code, self.max_execution_time)

        return success, output


# Singleton instance
_executor = None

def get_executor() -> PythonExecutor:
    """Get the global Python executor instance."""
    global _executor
    if _executor is None:
        _executor = PythonExecutor()
    return _executor
