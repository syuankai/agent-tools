"""Path validation policy for structured file tools.

Provides safe path validation that:
- Prevents path traversal (..)
- Prevents prefix collision (/workspace_evil != /workspace)
- Resolves symlinks and verifies they don't escape allowed roots
- Works for both read-only (v0.5.0) and future write operations
"""

from __future__ import annotations

import os
from pathlib import Path, PurePosixPath

from fastapi import HTTPException

# Allowed root directories. All file tool paths must resolve within one of these.
ALLOWED_ROOTS: tuple[str, ...] = ("/workspace", "/userfile")


class PathError(HTTPException):
    """Raised when a path fails validation."""

    def __init__(self, status: int, error: str, message: str):
        self.error_code = error
        self.message = message
        super().__init__(status, detail={"status": status, "error": error, "message": message})


def _normalize(path: str) -> str:
    """Normalize a path without resolving symlinks.

    Removes . and redundant slashes. Does NOT resolve symlinks.
    """
    p = PurePosixPath(path)
    parts: list[str] = []
    for part in p.parts:
        if part == ".":
            continue
        if part == "..":
            if parts and parts[-1] != "..":
                parts.pop()
            else:
                parts.append("..")
        else:
            parts.append(part)
    return str(PurePosixPath(*parts) if parts else ".")


def _is_under_root(resolved: str, root: str) -> bool:
    """Check if resolved path is strictly under a root.

    Uses trailing separator to prevent prefix collision:
    /workspace_evil is NOT under /workspace
    /workspace/file IS under /workspace
    """
    root = root.rstrip("/") + "/"
    resolved = resolved.rstrip("/") + "/"
    return resolved.startswith(root)


def _find_allowed_root(resolved: str) -> str | None:
    """Find which allowed root the resolved path belongs to.

    Returns the root path if found, None otherwise.
    """
    for root in ALLOWED_ROOTS:
        if _is_under_root(resolved, root) or resolved.rstrip("/") == root.rstrip("/"):
            return root
    return None


def validate_path(path: str, *, require_exists: bool = False) -> str:
    """Validate a file path against security policy.

    Args:
        path: The path to validate (absolute or relative).
        require_exists: If True, raise 404 if path doesn't exist.
                       If False, validate the path structure only.

    Returns:
        Resolved absolute path.

    Raises:
        PathError with appropriate status code:
        - 400: Invalid path (empty, null bytes, unparseable)
        - 403: Path outside allowed roots, or symlink escapes root
        - 404: Path not found (only if require_exists=True)
    """
    if not path:
        raise PathError(400, "invalid_path", "Path cannot be empty")

    if "\x00" in path:
        raise PathError(400, "invalid_path", "Path contains null byte")

    # Normalize first (without resolving symlinks)
    normalized = _normalize(path)

    # Must be absolute
    if not normalized.startswith("/"):
        raise PathError(400, "invalid_path", "Path must be absolute")

    # Check if the raw path (before symlink resolution) is under an allowed root.
    # This catches obvious cases like /workspace/file.
    raw_root = _find_allowed_root(normalized)
    if raw_root is None:
        raise PathError(
            403, "path_forbidden",
            f"Path outside allowed roots: {', '.join(ALLOWED_ROOTS)}"
        )

    # Resolve symlinks using realpath.
    # If the path doesn't exist, realpath returns the normalized path.
    try:
        resolved = os.path.realpath(normalized)
    except OSError as e:
        raise PathError(400, "invalid_path", f"Cannot resolve path: {e}")

    # After resolution, verify the path is still under an allowed root.
    # This catches symlink escapes.
    resolved_root = _find_allowed_root(resolved)
    if resolved_root is None:
        raise PathError(
            403, "path_forbidden",
            f"Path resolves outside allowed roots (symlink escape?)"
        )

    # Check existence if required
    if require_exists:
        if not os.path.exists(resolved):
            raise PathError(404, "not_found", f"Path not found: {path}")

    return resolved


def check_parent_exists(path: str) -> str:
    """Validate that the parent directory of a path exists.

    Useful for future write operations. For v0.5.0 read-only,
    this is not used but available for extension.

    Returns:
        Resolved absolute path of the target.

    Raises:
        PathError 404 if parent doesn't exist.
    """
    resolved = validate_path(path)
    parent = os.path.dirname(resolved)
    if not os.path.isdir(parent):
        raise PathError(404, "not_found", f"Parent directory not found: {parent}")
    return resolved


def is_binary(data: bytes, sample_size: int = 8192) -> bool:
    """Heuristic binary detection.

    Reads a sample of the file and checks for:
    - Null bytes (strong indicator)
    - High ratio of non-printable bytes

    Args:
        data: File content bytes.
        sample_size: Number of bytes to analyze.

    Returns:
        True if likely binary, False if likely text.
    """
    sample = data[:sample_size]

    if not sample:
        return False

    # Null bytes are a strong binary indicator
    if b"\x00" in sample:
        return True

    # Count non-printable, non-whitespace bytes
    non_printable = 0
    for byte in sample:
        # Control characters (except common whitespace: \t, \n, \r, \f, \v)
        if byte < 32 and byte not in (9, 10, 13, 12, 11):
            non_printable += 1
        # DEL character
        elif byte == 127:
            non_printable += 1

    # If more than 10% non-printable, likely binary
    if non_printable / len(sample) > 0.1:
        return True

    # Try UTF-8 decode
    try:
        sample.decode("utf-8")
    except UnicodeDecodeError:
        return True

    return False
