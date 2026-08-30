"""POST /file/read — Read a file's content as structured JSON."""

from __future__ import annotations

import os

from fastapi import APIRouter, Body, Header

from app.security.common import auth, output_limit
from app.security.path_policy import PathError, is_binary, validate_path

router = APIRouter()


@router.post("/file/read")
async def file_read(
    body: dict = Body(...),
    authorization: str | None = Header(None),
):
    auth(authorization)

    path = body.get("path")
    if not isinstance(path, str) or not path:
        raise PathError(400, "invalid_path", "path is required")

    resolved = validate_path(path, require_exists=True)

    if os.path.isdir(resolved):
        raise PathError(400, "is_directory", f"Cannot read directory: {path}. Use /file/list instead.")

    # Read in binary first for detection, then decode if text
    try:
        with open(resolved, "rb") as f:
            raw = f.read()
    except PermissionError:
        raise PathError(403, "permission_denied", f"Cannot read file: {path}")
    except OSError as e:
        raise PathError(500, "read_error", f"Failed to read file: {e}")

    file_size = len(raw)

    # Binary detection
    if is_binary(raw):
        raise PathError(
            400,
            "binary_file",
            f"Binary file detected ({file_size} bytes). Use /command to process binary files.",
        )

    # Try to decode as text
    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError:
        # Try other common encodings
        for enc in ("latin-1", "cp1252"):
            try:
                content = raw.decode(enc)
                break
            except UnicodeDecodeError:
                continue
        else:
            raise PathError(
                400,
                "encoding_error",
                f"Cannot decode file as text: {path}",
            )

    # Check truncation
    limit = output_limit()
    truncated = len(content.encode("utf-8", errors="replace")) > limit
    if truncated:
        data = content.encode("utf-8", errors="replace")[:limit]
        content = data.decode("utf-8", errors="replace") + "\n[output truncated]"

    return {
        "status": 200,
        "path": path,
        "resolved": resolved,
        "content": content,
        "size": file_size,
        "truncated": truncated,
    }
