"""POST /file/list — List directory contents as structured JSON."""

from __future__ import annotations

import os
from datetime import datetime, timezone

from fastapi import APIRouter, Body, Header

from app.security.common import auth
from app.security.path_policy import PathError, validate_path

router = APIRouter()

MAX_DIR_ENTRIES = max(10, int(os.getenv("MAX_DIR_ENTRIES", "1000")))


def _serialize_entry(entry: str, base: str) -> dict:
    """Serialize a directory entry to a JSON-friendly dict."""
    full = os.path.join(base, entry)
    try:
        st = os.lstat(full)
    except OSError:
        return {"name": entry, "error": "stat_failed"}

    is_link = os.path.islink(full)
    is_dir = os.path.isdir(full)
    is_file = os.path.isfile(full)

    try:
        modified = datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat()
    except (OSError, ValueError, OverflowError):
        modified = None

    return {
        "name": entry,
        "is_dir": is_dir,
        "is_file": is_file,
        "is_symlink": is_link,
        "size": st.st_size if not is_dir else 0,
        "modified": modified,
    }


@router.post("/file/list")
async def file_list(
    body: dict = Body(...),
    authorization: str | None = Header(None),
):
    auth(authorization)

    path = body.get("path", "/workspace")
    if not isinstance(path, str) or not path:
        raise PathError(400, "invalid_path", "path is required")

    resolved = validate_path(path, require_exists=True)

    if not os.path.isdir(resolved):
        raise PathError(400, "not_a_directory", f"Not a directory: {path}")

    try:
        entries_raw = os.listdir(resolved)
    except PermissionError:
        raise PathError(403, "permission_denied", f"Cannot list directory: {path}")

    truncated = len(entries_raw) > MAX_DIR_ENTRIES
    entries_raw = sorted(entries_raw)[:MAX_DIR_ENTRIES]

    entries = [_serialize_entry(e, resolved) for e in entries_raw]

    return {
        "status": 200,
        "path": path,
        "resolved": resolved,
        "entries": entries,
        "count": len(entries),
        "truncated": truncated,
    }
