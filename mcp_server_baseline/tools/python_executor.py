"""
Python code execution with baseline security.

✅ Implements: Block dangerous imports (os, subprocess, sys)
❌ Exploitable: __import__ not blocked, can bypass import restrictions
"""

import io
import sys
import logging

logger = logging.getLogger(__name__)


async def execute_python_tool(args: dict) -> str:
    """Execute Python code with baseline security checks."""
    code = args.get("code", "")

    # ✅ SECURITY: Input validation
    if not isinstance(code, str) or not code.strip():
        return "Error: Invalid code"

    # ✅ SECURITY: Block dangerous imports
    dangerous_imports = [
        'os',
        'subprocess',
        'sys',
        '__import__',  # Blocked here but...
        'eval',
        'exec',
        'compile',
        'open',  # Block direct file access
        'socket',
        'urllib',
        'requests',
        'http',
    ]

    code_lower = code.lower()
    for danger in dangerous_imports:
        if danger in code_lower:
            logger.warning(f"Blocked dangerous import/function: {danger}")
            return f"Error: Dangerous import or function not allowed: {danger}"

    # ❌ SECURITY GAP: Can use __import__("os") if written differently
    # ❌ SECURITY GAP: Can use getattr(__builtins__, 'eval')
    # ❌ SECURITY GAP: Can use chr() to build strings: chr(111)+chr(115) = "os"
    # ❌ SECURITY GAP: No AST analysis, just string matching

    try:
        logger.info(f"Executing Python code: {code[:100]}...")

        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = buffer = io.StringIO()

        # ✅ SECURITY: Use exec with restricted globals
        # ❌ SECURITY GAP: Still allows many builtins!
        restricted_globals = {
            '__builtins__': {
                'print': print,
                'len': len,
                'str': str,
                'int': int,
                'float': float,
                'list': list,
                'dict': dict,
                'range': range,
                'sum': sum,
                'max': max,
                'min': min,
                # ❌ SECURITY GAP: chr, ord can build arbitrary strings
                'chr': chr,
                'ord': ord,
                # ❌ SECURITY GAP: getattr can access hidden attributes
                'getattr': getattr,
                'hasattr': hasattr,
            }
        }

        exec(code, restricted_globals)

        sys.stdout = old_stdout
        output = buffer.getvalue()

        return output if output else "Code executed successfully (no output)"

    except Exception as e:
        sys.stdout = old_stdout
        return f"Error: {str(e)}"
