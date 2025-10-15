"""Command validation to prevent command injection attacks."""

import json
import shlex
from typing import Tuple, List


class CommandValidator:
    """Validates shell commands to prevent injection attacks."""

    def __init__(self, config_path: str = "/app/config/allowed_commands.json"):
        """Initialize validator with configuration."""
        with open(config_path, 'r') as f:
            config = json.load(f)

        self.allowed_commands = config['allowed_commands']
        self.dangerous_characters = config['dangerous_characters']

    def validate_command(self, command_str: str) -> Tuple[bool, str]:
        """
        Validate if a command is safe to execute.

        Returns:
            (is_valid, error_message)
        """
        # Check for dangerous characters (injection attempts)
        for dangerous_char in self.dangerous_characters:
            if dangerous_char in command_str:
                return False, f"Error: Dangerous character '{dangerous_char}' detected"

        try:
            # Parse command using shlex (handles quotes properly)
            parts = shlex.split(command_str)
        except ValueError as e:
            return False, f"Error: Invalid command syntax - {str(e)}"

        if not parts:
            return False, "Error: Empty command"

        base_command = parts[0]

        # Check if command is in allowed list
        if base_command not in self.allowed_commands:
            return False, f"Error: Command '{base_command}' is not allowed"

        # Get command config
        cmd_config = self.allowed_commands[base_command]

        # Validate command-specific rules
        if base_command == "curl":
            return self._validate_curl(parts[1:], cmd_config)
        elif base_command == "cat":
            return self._validate_cat(parts[1:], cmd_config)
        else:
            # Generic validation for other commands
            return self._validate_generic(parts[1:], cmd_config)

    def _validate_curl(self, args: List[str], config: dict) -> Tuple[bool, str]:
        """Validate curl command to prevent SSRF and file:// access."""
        if not args:
            return False, "Error: curl requires a URL argument"

        # Check for blocked protocols
        blocked_protocols = config.get('blocked_protocols', [])
        for arg in args:
            for protocol in blocked_protocols:
                if arg.lower().startswith(protocol):
                    return False, f"Error: Protocol '{protocol}' is not allowed"

        # Check for file:// protocol specifically
        for arg in args:
            if 'file://' in arg.lower():
                return False, "Error: file:// protocol is blocked"

        # Validate arguments
        allowed_args = config.get('allowed_args', [])
        for arg in args:
            # Skip URLs (they don't start with -)
            if not arg.startswith('-'):
                # Validate it's a proper HTTP/HTTPS URL
                if not (arg.startswith('http://') or arg.startswith('https://')):
                    return False, f"Error: Only HTTP/HTTPS URLs are allowed, got '{arg}'"
                continue

            # Check if flag is allowed
            if arg not in allowed_args:
                return False, f"Error: curl flag '{arg}' is not allowed"

        return True, ""

    def _validate_cat(self, args: List[str], config: dict) -> Tuple[bool, str]:
        """Validate cat command arguments."""
        if not args:
            return False, "Error: cat requires a file argument"

        if len(args) > 1:
            return False, "Error: cat can only read one file at a time"

        # Path validation will be done separately by PathValidator
        return True, ""

    def _validate_generic(self, args: List[str], config: dict) -> Tuple[bool, str]:
        """Generic validation for simple commands like ls, pwd, whoami."""
        allowed_args = config.get('allowed_args', [])

        # If no args are allowed and some were provided
        if not allowed_args and args:
            # Check if empty string is explicitly allowed (means no args)
            if "" in allowed_args:
                return False, f"Error: Command does not accept arguments"

        # Validate each argument
        for arg in args:
            if arg and arg not in allowed_args:
                return False, f"Error: Argument '{arg}' is not allowed"

        return True, ""

    def sanitize_output(self, output: str, max_length: int = 10000) -> str:
        """Sanitize command output to prevent information leakage."""
        if len(output) > max_length:
            output = output[:max_length] + f"\\n... (output truncated, {len(output)} bytes total)"

        return output
