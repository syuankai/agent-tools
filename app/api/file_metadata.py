"""POST /file/metadata — Get file/directory metadata as structured JSON."""

from __future__ import annotations

import os
import stat
from datetime import datetime, timezone

from fastapi import APIRouter, Body, Header

from app.security.common import auth
from app.security.path_policy import PathError, validate_path

router = APIRouter()


def _format_permissions(mode: int) -> str:
    """Format stat st_mode into a Unix permission string like -rwxr-xr-x."""
    if stat.S_ISLNK(mode):
        prefix = "l"
    elif stat.S_ISDIR(mode):
        prefix = "d"
    elif stat.S_ISREG(mode):
        prefix = "-"
    else:
        prefix = "?"

    perms = ""
    for who in ("USR", "GRP", "OTH"):
        for char, flag in (("r", stat.S_IRUSR), ("w", stat.S_IWUSR), ("x", stat.S_IXUSR)):
            offset = {"USR": 0, "GRP": 3, "OTH": 6}[who]
            if mode & (flag >> offset):
                perms += char
            else:
                perms += "-"
    return prefix + perms


@router.post("/file/metadata")
async def file_metadata(
    body: dict = Body(...),
    authorization: str | None = Header(None),
):
    auth(authorization)

    path = body.get("path")
    if not isinstance(path, str) or not path:
        raise PathError(400, "invalid_path", "path is required")

    resolved = validate_path(path, require_exists=True)

    try:
        st = os.lstat(resolved)
    except PermissionError:
        raise PathError(403, "permission_denied", f"Cannot stat: {path}")
    except OSError as e:
        raise PathError(500, "stat_error", str(e))

    is_link = os.path.islink(resolved)
    is_dir = os.path.isdir(resolved)
    is_file = os.path.isfile(resolved)

    try:
        modified = datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat()
    except (OSError, ValueError, OverflowError):
        modified = None

    try:
        created = datetime.fromtimestamp(st.st_ctime, tz=timezone.utc).isoformat()
    except (OSError, ValueError, OverflowError):
        created = None

    # Resolve symlink target if applicable
    symlink_target = None
    if is_link:
        try:
            symlink_target = os.readlink(resolved)
        except OSError:
            symlink_target = None

    return {
        "status": 200,
        "name": os.path.basename(resolved),
        "path": path,
        "resolved": resolved,
        "size": st.st_size if not is_dir else 0,
        "modified": modified,
        "created": created,
        "permissions": _format_permissions(st.st_mode),
        "is_dir": is_dir,
        "is_file": is_file,
        "is_symlink": is_link,
        "symlink_target": symlink_target,
    }
