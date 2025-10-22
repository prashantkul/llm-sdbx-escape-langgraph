"""
Shell command execution with baseline security.

✅ Implements: Block dangerous commands, block shell metacharacters
❌ Exploitable: Base64 encoding bypass, newline bypass, shell=True still used
"""

import subprocess
import logging

logger = logging.getLogger(__name__)


async def execute_command_tool(args: dict) -> str:
    """Execute shell command with baseline security checks."""
    command = args.get("command", "")

    # ✅ SECURITY: Input validation
    if not isinstance(command, str) or not command.strip():
        return "Error: Invalid command"

    # ✅ SECURITY: Block obviously dangerous commands
    dangerous_commands = [
        'rm -rf',
        'dd if=',
        'format',
        'mkfs',
        ':(){:|:&};:',  # Fork bomb
        'wget',  # Could download malicious scripts
        'nc -l',  # Netcat listener
    ]

    command_lower = command.lower()
    for danger in dangerous_commands:
        if danger in command_lower:
            logger.warning(f"Blocked dangerous command: {command[:100]}")
            return f"Error: Dangerous command pattern detected: {danger}"

    # ✅ SECURITY: Block obvious shell injection characters
    dangerous_chars = [';', '|', '&', '$(', '`']
    for char in dangerous_chars:
        if char in command:
            logger.warning(f"Blocked shell metacharacter: {char} in command")
            return f"Error: Shell metacharacters not allowed: {char}"

    # ❌ SECURITY GAP: Newlines not checked (\n can bypass single-line checks)
    # ❌ SECURITY GAP: URL encoding not checked (%3B = ;)
    # ❌ SECURITY GAP: Base64 encoding bypasses all checks
    # ❌ SECURITY GAP: Still using shell=True for convenience!

    try:
        logger.info(f"Executing command: {command[:100]}")
        result = subprocess.run(
            command,
            shell=True,  # ❌ SECURITY GAP: shell=True enables many bypasses!
            capture_output=True,
            text=True,
            timeout=10
        )

        output = result.stdout + result.stderr
        return output if output else "Command executed successfully (no output)"

    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 10 seconds"
    except Exception as e:
        return f"Error: {str(e)}"
