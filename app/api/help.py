from fastapi import APIRouter
import os
from app.security.command_policy import blocked_commands
from app.security.common import output_limit

router = APIRouter()


def _env_int(name: str, default: int) -> int:
    return max(1, int(os.getenv(name, str(default))))


@router.get("/help")
async def help():
    return {
        "version": os.getenv("APP_VERSION", "0.0.5"),
        "endpoints": {
            "POST /command": "Execute commands inside the Tool Server; system/custom blocked commands are forbidden. /command and /file behave identically.",
            "POST /file": "Alias for /command. Executes shell commands inside the Tool Server with the same policy.",
            "POST /filepc": "Operate only inside the host directory exposed as /userfile via a disposable restricted container.",
            "POST /commandpc": "Create a temporary SSH connection to the configured host account and execute one command.",
            "POST /proc": "Read-only host proc inspection via /hostproc; unsafe operations return 403.",
            "POST /docker": "Execute a Docker command through the mounted Docker socket; Docker mutations are disabled by default.",
            "POST /getfile": "Download a public HTTP/HTTPS URL into /aifile with SSRF and size protections.",
            "GET /env": "Read only allowlisted container environment variables; secrets are redacted by default.",
            "GET /health": "Unauthenticated health check.",
            "GET /stats": "Authenticated in-process request/tool statistics.",
            "GET /help": "Show this help message.",
        },
        "responses": {
            "success_with_output": "HTTP 200 + {status: 200, output: \"...\"}",
            "success_with_exit_code": "HTTP 200 + {status: 200, output: \"...\", exit_code: N} — command ran but returned non-zero",
            "forbidden": "HTTP 403 — command blocked by policy",
            "rate_limited": "HTTP 429 + Retry-After header",
            "timeout": "HTTP 504 — command exceeded timeout",
            "body_too_large": "HTTP 413 — request body exceeds limit",
        },
        "limits": {
            "rate_limit": f"{_env_int('RATE_LIMIT_REQUESTS', 30)} requests per {_env_int('RATE_LIMIT_WINDOW', 60)} seconds",
            "max_concurrent_tools": str(_env_int('MAX_CONCURRENT_TOOLS', 4)),
            "max_body_bytes": f"{_env_int('MAX_BODY_BYTES', 65536)} bytes ({_env_int('MAX_BODY_BYTES', 65536) // 1024} KB)",
            "max_output_size": f"{output_limit()} bytes ({output_limit() // 1024} KB)",
            "max_file_size": f"{_env_int('MAX_FILE_SIZE', 104857600)} bytes ({_env_int('MAX_FILE_SIZE', 104857600) // 1048576} MB)",
            "command_timeout": f"{_env_int('COMMAND_TIMEOUT', 30)} seconds",
            "filepc_timeout": f"{_env_int('FILEPC_TIMEOUT', 120)} seconds",
            "commandpc_timeout": f"{_env_int('COMMANDPC_TIMEOUT', 30)} seconds",
            "docker_timeout": f"{_env_int('DOCKER_TIMEOUT', 120)} seconds",
            "download_timeout": f"{_env_int('DOWNLOAD_TIMEOUT', 300)} seconds",
            "per_task_call_limit": str(_env_int('MAX_TOOL_CALLS', 20)),
        },
        "command_policy": {
            "blocked_commands": sorted(blocked_commands()),
            "note": "rm is always blocked and cannot be removed from BLOCK env.",
        },
    }
