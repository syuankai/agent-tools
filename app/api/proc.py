from fastapi import APIRouter, Header, HTTPException
import subprocess
from app.security.common import auth, result
from app.security.proc_policy import check_proc

router = APIRouter()

@router.post("/proc")
async def proc(body: str, authorization: str | None = Header(None)):
    auth(authorization)
    if not check_proc(body):
        raise HTTPException(403, "/proc is read-only.")
    if "/proc" in body and "/hostproc" not in body:
        body = body.replace("/proc", "/hostproc")
    if not body.strip():
        raise HTTPException(400, "Command required.")
    try:
        p = subprocess.run(
            ["/bin/sh", "-c", body],
            capture_output=True, text=True, timeout=30,
            cwd="/workspace",
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(504, "Command timed out.")
    out = (p.stdout + p.stderr).strip()
    return result(out, p.returncode)
