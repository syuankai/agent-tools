from fastapi import APIRouter, Body, Header, HTTPException
import os
import paramiko
from app.security.common import auth, result, trim_output
from app.security.command_policy import check_command

router = APIRouter()

@router.post("/commandpc")
async def commandpc(body: str = Body(...), authorization: str | None = Header(None)):
    auth(authorization)
    ok, blocked = check_command(body)
    if not ok:
        raise HTTPException(403, f"Command blocked by policy: {blocked or 'unsafe command'}")

    host = os.environ["COMMANDPC_HOST"]
    port = int(os.getenv("COMMANDPC_PORT", "22"))
    user = os.environ["COMMANDPC_USER"]
    keyfile = os.environ["COMMANDPC_KEY_FILE"]
    if not os.path.isfile(keyfile):
        raise HTTPException(500, "SSH key file not found.")

    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.RejectPolicy())
    timeout = int(os.getenv("COMMANDPC_TIMEOUT", "30"))
    try:
        client.connect(
            hostname=host, port=port, username=user, key_filename=keyfile,
            timeout=15, auth_timeout=15, banner_timeout=15,
        )
        stdin, stdout, stderr = client.exec_command(body, timeout=timeout)
        out = trim_output(
            (stdout.read().decode(errors="replace") + stderr.read().decode(errors="replace")).strip()
        )
        code = stdout.channel.recv_exit_status()
        return result(out, code)
    except paramiko.ssh_exception.SSHException as e:
        raise HTTPException(502, f"SSH error: {e}")
    finally:
        client.close()
