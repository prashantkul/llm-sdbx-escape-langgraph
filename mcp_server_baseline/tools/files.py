"""
File operations with baseline security.

✅ Implements: Basic validation, blocks obvious sensitive files
❌ Exploitable: Path traversal, /etc/passwd not blocked, symlink following
"""

import os
import logging

logger = logging.getLogger(__name__)


async def read_file_tool(args: dict) -> str:
    """Read file with baseline security checks."""
    path = args.get("path", "")

    # ✅ SECURITY: Input validation
    if not isinstance(path, str):
        return "Error: Path must be a string"

    if not path or not path.strip():
        return "Error: Path cannot be empty"

    # ✅ SECURITY: Block obvious sensitive files
    sensitive_patterns = [
        '/etc/shadow',
        '/etc/sudoers',
        '/root/.bash_history',
        # Note: /etc/passwd NOT in list - exploitable gap!
    ]

    for pattern in sensitive_patterns:
        if pattern in path:
            logger.warning(f"Blocked access to sensitive file: {path}")
            return f"Error: Access denied - sensitive file pattern detected"

    # ✅ SECURITY: Check file exists
    # ❌ SECURITY GAP: os.path.exists follows symlinks!
    if not os.path.exists(path):
        return f"Error: File not found: {path}"

    # ❌ SECURITY GAP: No path traversal prevention (../ works)
    # ❌ SECURITY GAP: No symlink resolution
    # ❌ SECURITY GAP: No allowlist of directories

    try:
        logger.info(f"Reading file: {path}")
        with open(path, 'r') as f:
            content = f.read()
            return content
    except PermissionError:
        return f"Error: Permission denied: {path}"
    except Exception as e:
        return f"Error: {str(e)}"


async def write_file_tool(args: dict) -> str:
    """Write file with baseline security checks."""
    path = args.get("path", "")
    content = args.get("content", "")

    # ✅ SECURITY: Input validation
    if not isinstance(path, str) or not isinstance(content, str):
        return "Error: Path and content must be strings"

    if not path.strip():
        return "Error: Path cannot be empty"

    # ✅ SECURITY: Block writing to system directories
    dangerous_dirs = ['/etc/', '/usr/', '/bin/', '/sbin/', '/boot/']
    if any(path.startswith(d) for d in dangerous_dirs):
        logger.warning(f"Blocked write to system directory: {path}")
        return f"Error: Cannot write to system directories"

    # ❌ SECURITY GAP: Can write to /tmp, /app (useful for staged attacks)
    # ❌ SECURITY GAP: No path traversal prevention

    try:
        logger.info(f"Writing to file: {path}")
        with open(path, 'w') as f:
            f.write(content)
        return f"Successfully wrote {len(content)} bytes to {path}"
    except PermissionError:
        return f"Error: Permission denied: {path}"
    except Exception as e:
        return f"Error: {str(e)}"
