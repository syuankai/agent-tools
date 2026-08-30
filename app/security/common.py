from __future__ import annotations

import os
from fastapi import HTTPException


def auth(authorization: str | None):
    key = os.getenv("API_KEY")
    if not key:
        raise HTTPException(500, "API_KEY is not configured")
    if authorization != f"Bearer {key}":
        raise HTTPException(401, "Unauthorized")


def result(output="", code=0):
    output = output or ""
    if code == 0:
        return {"status": 200, "output": output or "All done."}
    return {"status": 500, "output": output or "Command failed.", "exit_code": code}


def output_limit() -> int:
    return max(1024, int(os.getenv("MAX_OUTPUT_SIZE", "1048576")))


def trim_output(output: str) -> str:
    limit = output_limit()
    if len(output.encode("utf-8", errors="replace")) <= limit:
        return output
    data = output.encode("utf-8", errors="replace")[:limit]
    return data.decode("utf-8", errors="replace") + "\n[output truncated]"
