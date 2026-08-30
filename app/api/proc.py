from fastapi import APIRouter, Body, Header, HTTPException
import re
import subprocess
from app.security.common import auth, result, trim_output
from app.security.proc_policy import check_proc

router = APIRouter()

_REWRITE_PATTERN = re.compile(r"(?<![/\w])/proc(?=/|$)")


def _rewrite_proc(cmd: str) -> str:
    """Rewrite /proc → /hostproc only for actual /proc paths.

    Matches /proc followed by / or end-of-string, but NOT /proc followed by
    lowercase letters (e.g. /procinfo stays as-is).
    """
    return _REWRITE_PATTERN.sub("/hostproc", cmd)


@router.post("/proc")
async def proc(body: str = Body(...), authorization: str | None = Header(None)):
    auth(authorization)
    # Rewrite /proc → /hostproc before policy check, so the allowlist
    # can validate the actual paths that will be used at runtime.
    rewritten = _rewrite_proc(body)
    if not check_proc(rewritten):
        raise HTTPException(403, "/proc is read-only.")
    if not rewritten.strip():
        raise HTTPException(400, "Command required.")
    try:
        p = subprocess.run(
            ["/bin/sh", "-c", rewritten],
            capture_output=True, text=True, timeout=30,
            cwd="/workspace",
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(504, "Command timed out.")
    out = trim_output((p.stdout + p.stderr).strip())
    return result(out, p.returncode)
