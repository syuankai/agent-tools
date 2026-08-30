from fastapi import APIRouter, Header, HTTPException
import os
import subprocess
from app.security.common import auth, result, trim_output
from app.security.command_policy import check_command
from app.security.filepc_policy import check_filepc

router = APIRouter()
FILEPC_IMAGE = os.getenv("FILEPC_IMAGE", "ubuntu:24.04")

@router.post("/filepc")
async def filepc(body: str, authorization: str | None = Header(None)):
    auth(authorization)
    if not body.strip():
        raise HTTPException(400, "Command required.")
    ok, blocked = check_command(body)
    if not ok:
        raise HTTPException(403, f"Command blocked by policy: {blocked or 'unsafe command'}")
    ok, reason = check_filepc(body)
    if not ok:
        raise HTTPException(403, f"/filepc policy: {reason}")

    source = os.environ["USERFILE_HOST_PATH"]
    if not os.path.isabs(source):
        raise HTTPException(500, "USERFILE_HOST_PATH must be an absolute host path.")

    args = [
        "docker", "run", "--rm", "--network", "none", "--read-only",
        "--cap-drop=ALL", "--security-opt", "no-new-privileges",
        "--mount", f"type=bind,src={source},dst=/userfile",
        "--workdir", "/userfile", FILEPC_IMAGE, "/bin/sh", "-c", body
    ]
    timeout = int(os.getenv("FILEPC_TIMEOUT", "120"))
    try:
        p = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise HTTPException(504, "File operation timed out.")
    out = trim_output((p.stdout + p.stderr).strip())
    return result(out, p.returncode)
