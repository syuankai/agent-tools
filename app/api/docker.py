from fastapi import APIRouter, Header, HTTPException
import os
import shlex
import subprocess
from app.security.common import auth, result, trim_output
from app.security.command_policy import check_command

router = APIRouter()

@router.post("/docker")
async def docker(body: str, authorization: str | None = Header(None)):
    auth(authorization)
    try:
        args = shlex.split(body)
    except ValueError:
        raise HTTPException(400, "Invalid shell syntax.")
    if not args or args[0] != "docker":
        raise HTTPException(400, "Body must start with 'docker'.")

    # Apply the global BLOCK policy to the docker command/subcommand too.
    ok, blocked = check_command(body)
    if not ok:
        raise HTTPException(403, f"Command blocked by policy: {blocked or 'unsafe command'}")

    if os.getenv("ALLOW_DOCKER_MUTATION", "false").lower() not in {"1", "true", "yes", "on"}:
        if len(args) > 1 and args[1] in {
            "run", "create", "start", "stop", "restart", "kill", "rm", "rmi",
            "rename", "update", "exec", "cp", "build", "push", "pull",
        }:
            raise HTTPException(403, f"Docker mutation is disabled: {args[1]}")

    timeout = int(os.getenv("DOCKER_TIMEOUT", "120"))
    try:
        p = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise HTTPException(504, "Docker command timed out.")
    out = trim_output((p.stdout + p.stderr).strip())
    return result(out, p.returncode)
