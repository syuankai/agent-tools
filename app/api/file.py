from fastapi import APIRouter, Header, HTTPException
import os
import subprocess
from app.security.common import auth, result, trim_output
from app.security.command_policy import check_command

router = APIRouter()

@router.post("/file")
async def file(body: str, authorization: str | None = Header(None)):
    auth(authorization)
    ok, blocked = check_command(body)
    if not ok:
        raise HTTPException(403, f"Command blocked by policy: {blocked or 'unsafe command'}")
    timeout = int(os.getenv("COMMAND_TIMEOUT", "30"))
    try:
        p = subprocess.run(
            ["/bin/sh", "-c", body], capture_output=True, text=True,
            timeout=timeout, cwd="/workspace",
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(504, "Command timed out.")
    out = trim_output((p.stdout + p.stderr).strip())
    return result(out, p.returncode)
