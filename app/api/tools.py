from fastapi import APIRouter, Header
import os
from app.security.common import auth, output_limit
from app.security.command_policy import blocked_commands

router = APIRouter()


def _env_int(name: str, default: int) -> int:
    return max(1, int(os.getenv(name, str(default))))


def _tool_defs() -> list[dict]:
    """Return structured tool definitions for Agent auto-discovery."""
    common_limits = {
        "rate_limit": f"{_env_int('RATE_LIMIT_REQUESTS', 30)} requests per {_env_int('RATE_LIMIT_WINDOW', 60)}s",
        "max_body_bytes": _env_int('MAX_BODY_BYTES', 65536),
        "max_output_bytes": output_limit(),
        "max_concurrent": _env_int('MAX_CONCURRENT_TOOLS', 4),
        "per_task_call_limit": _env_int('MAX_TOOL_CALLS', 20),
    }
    blocked = sorted(blocked_commands())

    return [
        {
            "name": "command",
            "method": "POST",
            "path": "/command",
            "description": "Execute a shell command inside the Tool Server container.",
            "when_to_use": "Run commands in the container environment (shell, scripts, file operations, git, npm, etc.).",
            "input": {"type": "text/plain", "example": "ls -la /workspace"},
            "output": {
                "type": "application/json",
                "schema": {"status": 200, "output": "string", "exit_code": "int (present when non-zero)"},
            },
            "examples": [
                {"description": "List files", "body": "ls -la /workspace"},
                {"description": "Run a script", "body": "bash /workspace/script.sh"},
                {"description": "Check git status", "body": "cd /workspace && git status"},
            ],
            "timeout_seconds": _env_int('COMMAND_TIMEOUT', 30),
            "security": {
                "blocked_commands": blocked,
                "note": "rm is always blocked. Other commands blocked via BLOCK env.",
                "mutation_allowed": False,
            },
            "limits": common_limits,
            "retry_safe": True,
            "notes": "Identical to /file. Use /command or /file interchangeably.",
        },
        {
            "name": "file",
            "method": "POST",
            "path": "/file",
            "description": "Alias for /command. Executes shell commands with the same policy.",
            "when_to_use": "Equivalent to /command. Kept for backward compatibility.",
            "input": {"type": "text/plain", "example": "cat data.csv | head -5"},
            "output": {
                "type": "application/json",
                "schema": {"status": 200, "output": "string", "exit_code": "int (present when non-zero)"},
            },
            "timeout_seconds": _env_int('COMMAND_TIMEOUT', 30),
            "security": {
                "blocked_commands": blocked,
                "note": "Identical policy to /command.",
                "mutation_allowed": False,
            },
            "limits": common_limits,
            "retry_safe": True,
            "notes": "Alias for /command. Prefer /command for clarity.",
        },
        {
            "name": "filepc",
            "method": "POST",
            "path": "/filepc",
            "description": "Execute file operations inside a disposable, isolated container with access to a host directory.",
            "when_to_use": "Safely operate on files in the host directory mapped to /userfile. Network is disabled, filesystem is read-only.",
            "input": {"type": "text/plain", "example": "cat /userfile/data.txt"},
            "output": {
                "type": "application/json",
                "schema": {"status": 200, "output": "string", "exit_code": "int (present when non-zero)"},
            },
            "examples": [
                {"description": "Read a file", "body": "cat /userfile/config.json"},
                {"description": "List directory", "body": "ls -la /userfile"},
                {"description": "Search in files", "body": "grep -r 'pattern' /userfile"},
            ],
            "timeout_seconds": _env_int('FILEPC_TIMEOUT', 120),
            "security": {
                "blocked_commands": blocked,
                "extra_policy": "Commands limited to cat, ls, head, tail, grep, find, sed, etc. Paths restricted to /userfile.",
                "network": "none",
                "filesystem": "read-only",
                "capabilities": "dropped",
                "mutation_allowed": False,
            },
            "limits": common_limits,
            "retry_safe": True,
            "notes": "Use for file operations that need host directory access. More restricted than /command.",
        },
        {
            "name": "commandpc",
            "method": "POST",
            "path": "/commandpc",
            "description": "Execute a command on a remote host via SSH.",
            "when_to_use": "Run commands on the configured SSH host (e.g., the host machine). Requires SSH key configuration.",
            "input": {"type": "text/plain", "example": "uname -a"},
            "output": {
                "type": "application/json",
                "schema": {"status": 200, "output": "string", "exit_code": "int (present when non-zero)"},
            },
            "timeout_seconds": _env_int('COMMANDPC_TIMEOUT', 30),
            "security": {
                "blocked_commands": blocked,
                "note": "SSH host key must be pre-configured. Unknown hosts are rejected.",
                "mutation_allowed": True,
            },
            "limits": common_limits,
            "retry_safe": True,
            "requires_config": ["COMMANDPC_HOST", "COMMANDPC_USER", "COMMANDPC_KEY_FILE"],
            "notes": "Connects to remote host via SSH. Each invocation creates a new connection.",
        },
        {
            "name": "proc",
            "method": "POST",
            "path": "/proc",
            "description": "Read-only inspection of host /proc filesystem (CPU, memory, processes).",
            "when_to_use": "Check host system status: CPU info, memory usage, process list, uptime, etc.",
            "input": {"type": "text/plain", "example": "cat /proc/cpuinfo | head -20"},
            "output": {
                "type": "application/json",
                "schema": {"status": 200, "output": "string", "exit_code": "int (present when non-zero)"},
            },
            "timeout_seconds": 30,
            "security": {
                "allowed_commands": ["cat", "ls", "head", "tail", "grep", "rg", "sort", "wc", "cut", "tr", "stat", "readlink", "realpath", "pwd", "find", "sed"],
                "note": "Strictly read-only. Only whitelisted commands allowed. /proc paths are rewritten to /hostproc.",
                "mutation_allowed": False,
            },
            "limits": common_limits,
            "retry_safe": True,
            "requires_config": ["Host /proc must be mounted as /hostproc in the container."],
            "notes": "Only works if /hostproc is mounted. Commands are strictly read-only.",
        },
        {
            "name": "docker",
            "method": "POST",
            "path": "/docker",
            "description": "Execute Docker commands via the mounted Docker socket.",
            "when_to_use": "Query or manage Docker containers, images, networks. Mutations are disabled by default.",
            "input": {"type": "text/plain", "example": "docker ps"},
            "output": {
                "type": "application/json",
                "schema": {"status": 200, "output": "string", "exit_code": "int (present when non-zero)"},
            },
            "examples": [
                {"description": "List running containers", "body": "docker ps"},
                {"description": "List all containers", "body": "docker ps -a"},
                {"description": "List images", "body": "docker images"},
            ],
            "timeout_seconds": _env_int('DOCKER_TIMEOUT', 120),
            "security": {
                "blocked_commands": blocked,
                "mutation_blocked": ["run", "create", "start", "stop", "restart", "kill", "rm", "rmi", "rename", "update", "exec", "cp", "build", "push", "pull", "compose"],
                "note": "Mutations blocked by default. Enable via ALLOW_DOCKER_MUTATION=true.",
                "mutation_allowed": False,
            },
            "limits": common_limits,
            "retry_safe": True,
            "notes": "Read-only by default. Use for docker ps, docker images, docker inspect, etc.",
        },
        {
            "name": "getfile",
            "method": "POST",
            "path": "/getfile",
            "description": "Download a file from a public HTTP/HTTPS URL into the /aifile directory.",
            "when_to_use": "Download datasets, models, or other files from the internet.",
            "input": {"type": "text/plain", "example": "https://example.com/data.csv"},
            "output": {
                "type": "application/json",
                "schema": {"status": 200, "output": "Downloaded: /aifile/filename"},
            },
            "examples": [
                {"description": "Download a CSV", "body": "https://example.com/data.csv"},
                {"description": "Download a JSON file", "body": "https://api.example.com/config.json"},
            ],
            "timeout_seconds": _env_int('DOWNLOAD_TIMEOUT', 300),
            "security": {
                "ssrf_protection": True,
                "private_ip_blocked": True,
                "max_redirects": 5,
                "mutation_allowed": False,
            },
            "limits": {
                **common_limits,
                "max_file_size": f"{_env_int('MAX_FILE_SIZE', 104857600)} bytes",
            },
            "retry_safe": True,
            "notes": "Downloads to /aifile/. SSRF-protected: private/internal IPs blocked.",
        },
        {
            "name": "env",
            "method": "GET",
            "path": "/env",
            "description": "Read allowlisted container environment variables.",
            "when_to_use": "Check configuration, API keys (redacted), or environment state.",
            "input": None,
            "output": {
                "type": "application/json",
                "schema": {"status": 200, "variables": {"KEY": "value"}},
            },
            "security": {
                "allowlist": os.getenv("ENV_ALLOWLIST", ""),
                "redact_secrets": os.getenv("ENV_REDACT", "true").lower() in {"1", "true", "yes", "on"},
                "mutation_allowed": False,
            },
            "retry_safe": True,
            "notes": "Only returns variables in ENV_ALLOWLIST. Secrets are redacted.",
        },
        {
            "name": "stats",
            "method": "GET",
            "path": "/stats",
            "description": "View server request statistics and uptime.",
            "when_to_use": "Monitor server health, check request counts, or diagnose rate limiting.",
            "input": None,
            "output": {
                "type": "application/json",
                "schema": {"status": 200, "requests": "int", "tool_calls": "int", "errors": "int", "rate_limited": "int", "uptime_seconds": "float"},
            },
            "retry_safe": True,
            "notes": "In-memory counters. Reset on server restart.",
        },
        {
            "name": "health",
            "method": "GET",
            "path": "/health",
            "description": "Unauthenticated health check.",
            "when_to_use": "Verify the server is running. No authentication required.",
            "input": None,
            "output": {
                "type": "application/json",
                "schema": {"status": "ok", "version": "string"},
            },
            "retry_safe": True,
            "notes": "No authentication required. Useful for connectivity checks.",
        },
    ]


@router.get("/tools")
async def tools(authorization: str | None = Header(None)):
    auth(authorization)
    return {
        "version": os.getenv("APP_VERSION", "0.0.4"),
        "tools": _tool_defs(),
        "global_limits": {
            "rate_limit": f"{_env_int('RATE_LIMIT_REQUESTS', 30)} requests per {_env_int('RATE_LIMIT_WINDOW', 60)} seconds",
            "max_concurrent_tools": _env_int('MAX_CONCURRENT_TOOLS', 4),
            "max_body_bytes": _env_int('MAX_BODY_BYTES', 65536),
            "max_output_bytes": output_limit(),
            "per_task_call_limit": _env_int('MAX_TOOL_CALLS', 20),
        },
        "authentication": {
            "type": "Bearer token",
            "header": "Authorization: Bearer <API_KEY>",
        },
        "error_format": {
            "success": {"status": 200, "output": "string"},
            "command_failed": {"status": 200, "output": "string", "exit_code": "int"},
            "forbidden": {"detail": "string"},
            "rate_limited": {"status": 429, "output": "string", "Retry-After": "int"},
            "timeout": {"detail": "string"},
        },
    }
