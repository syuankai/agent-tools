from fastapi import APIRouter
import os
from app.security.command_policy import blocked_commands

router = APIRouter()

@router.get("/help")
async def help():
    return {
        "version": os.getenv("APP_VERSION", "0.3.0"),
        "endpoints": {
            "POST /docker": "Execute a Docker command through the mounted Docker socket; Docker mutations are disabled by default.",
            "POST /file": "Execute file/shell operations inside the Tool Server; system/custom blocked commands are forbidden.",
            "POST /filepc": "Operate only inside the host directory exposed as /userfile via a disposable restricted container.",
            "POST /command": "Execute commands inside the Tool Server; system/custom blocked commands are forbidden.",
            "POST /commandpc": "Create a temporary SSH connection to the configured host account and execute one command.",
            "POST /proc": "Read-only host proc inspection via /hostproc; unsafe operations return 403.",
            "POST /getfile": "Download a public HTTP/HTTPS URL into /aifile with SSRF and size protections.",
            "GET /env": "Read only allowlisted container environment variables; secrets are redacted by default.",
            "GET /health": "Unauthenticated health check.",
            "GET /stats": "Authenticated in-process request/tool statistics.",
            "GET /help": "Show API usage and active command policy.",
        },
        "responses": {
            "success_with_output": "HTTP 200 + output",
            "success_without_output": "HTTP 200 + All done.",
            "forbidden": "HTTP 403",
            "rate_limited": "HTTP 429 + Retry-After",
            "timeout": "HTTP 504",
        },
        "limits": {
            "rate_limit_requests": "RATE_LIMIT_REQUESTS per RATE_LIMIT_WINDOW seconds",
            "max_concurrent_tools": "MAX_CONCURRENT_TOOLS",
            "max_body_bytes": "MAX_BODY_BYTES",
            "max_output_size": "MAX_OUTPUT_SIZE",
            "max_file_size": "MAX_FILE_SIZE",
        },
        "command_policy": {
            "blocked_commands": sorted(blocked_commands()),
            "block_environment_variable": "BLOCK=rm,apt,npm",
            "note": "rm is always blocked and cannot be removed from policy.",
        },
    }
