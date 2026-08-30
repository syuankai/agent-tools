"""POST /file/search — Search for files using glob patterns."""

from __future__ import annotations

import fnmatch
import os

from fastapi import APIRouter, Body, Header

from app.security.common import auth
from app.security.path_policy import PathError, validate_path

router = APIRouter()

MAX_SEARCH_RESULTS = max(10, int(os.getenv("MAX_SEARCH_RESULTS", "500")))
MAX_SEARCH_DEPTH = max(1, int(os.getenv("MAX_SEARCH_DEPTH", "10")))


def _search(root: str, pattern: str, entry_type: str, max_results: int) -> tuple[list[str], bool]:
    """Recursively search for files matching a glob pattern.

    Returns (matches, truncated).
    """
    matches: list[str] = []
    truncated = False

    def _walk(directory: str, depth: int) -> None:
        nonlocal truncated
        if truncated or depth > MAX_SEARCH_DEPTH:
            return

        try:
            entries = sorted(os.scandir(directory), key=lambda e: e.name)
        except PermissionError:
            return

        for entry in entries:
            if truncated:
                return

            name = entry.name
            full_path = entry.path

            # Check if name matches pattern
            if fnmatch.fnmatch(name, pattern):
                include = False
                if entry_type == "file" and entry.is_file(follow_symlinks=False):
                    include = True
                elif entry_type == "dir" and entry.is_dir(follow_symlinks=False):
                    include = True
                elif entry_type == "all":
                    include = True

                if include:
                    matches.append(full_path)
                    if len(matches) >= max_results:
                        truncated = True
                        return

            # Recurse into directories (but not symlinks to directories)
            if entry.is_dir(follow_symlinks=False):
                _walk(full_path, depth + 1)

    _walk(root, 0)
    return matches, truncated


@router.post("/file/search")
async def file_search(
    body: dict = Body(...),
    authorization: str | None = Header(None),
):
    auth(authorization)

    path = body.get("path", "/workspace")
    pattern = body.get("pattern", "*")
    entry_type = body.get("type", "file")

    if not isinstance(path, str) or not path:
        raise PathError(400, "invalid_path", "path is required")

    if not isinstance(pattern, str) or not pattern:
        raise PathError(400, "invalid_pattern", "pattern is required")

    if entry_type not in ("file", "dir", "all"):
        raise PathError(400, "invalid_type", "type must be 'file', 'dir', or 'all'")

    resolved = validate_path(path, require_exists=True)

    if not os.path.isdir(resolved):
        raise PathError(400, "not_a_directory", f"Not a directory: {path}")

    matches, truncated = _search(resolved, pattern, entry_type, MAX_SEARCH_RESULTS)

    return {
        "status": 200,
        "path": path,
        "pattern": pattern,
        "type": entry_type,
        "matches": matches,
        "count": len(matches),
        "truncated": truncated,
    }
