"""Path validation to prevent directory traversal attacks."""

import os
import json
from pathlib import Path
from typing import Tuple


class PathValidator:
    """Validates file paths to prevent escape attempts."""

    def __init__(self, config_path: str = "/app/config/allowed_paths.json"):
        """Initialize validator with configuration."""
        with open(config_path, 'r') as f:
            config = json.load(f)

        self.allowed_paths = [Path(p).resolve() for p in config['allowed_paths']]
        self.blocked_patterns = config['blocked_patterns']

    def validate_path(self, user_path: str) -> Tuple[bool, str, str]:
        """
        Validate if a path is safe to access.

        Returns:
            (is_valid, resolved_path, error_message)
        """
        # Check for null bytes (common bypass technique)
        if '\x00' in user_path:
            return False, "", "Error: Null bytes detected in path"

        # Check blocked patterns first
        for pattern in self.blocked_patterns:
            if pattern in user_path:
                return False, "", f"Error: Access denied - blocked pattern '{pattern}' detected"

        try:
            # Resolve to absolute path (handles .., symlinks, etc.)
            resolved = Path(user_path).resolve()

            # Check if resolved path starts with any allowed path
            for allowed_path in self.allowed_paths:
                try:
                    resolved.relative_to(allowed_path)
                    # Path is within allowed directory
                    return True, str(resolved), ""
                except ValueError:
                    # Path is not relative to this allowed_path, try next
                    continue

            # No allowed path matched
            return False, "", f"Error: Access denied - path '{user_path}' is outside allowed directories"

        except Exception as e:
            return False, "", f"Error: Invalid path - {str(e)}"

    def check_symlink_chain(self, file_path: str) -> Tuple[bool, str]:
        """
        Check if path contains symlinks that escape allowed directories.

        Returns:
            (is_safe, error_message)
        """
        try:
            path = Path(file_path)

            # Check each component of the path
            current = Path('/')
            for part in path.parts[1:]:  # Skip root
                current = current / part

                if current.is_symlink():
                    target = current.readlink()
                    # Check if symlink target is valid
                    is_valid, _, error = self.validate_path(str(target))
                    if not is_valid:
                        return False, f"Error: Symlink '{current}' points to restricted location"

            return True, ""

        except Exception as e:
            return False, f"Error checking symlinks: {str(e)}"
