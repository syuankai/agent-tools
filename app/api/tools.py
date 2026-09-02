"""GET /tools — Agent auto-discovery endpoint with structured tool catalog."""

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
        # === Structured File Tools (v0.0.5) ===
        {
            "name": "file/list",
            "method": "POST",
            "path": "/file/list",
            "description": "List directory contents as structured JSON.",
            "when_to_use": "Discover what files exist in /workspace or /userfile. Returns names, sizes, types, and modification times. Always prefer this over /command with 'ls'.",
            "when_not_to_use": "When you need to read file contents (use /file/read), search for files (use /file/search), or execute shell commands (use /command).",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path", "default": "/workspace"}
                },
                "required": ["path"],
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "status": {"type": "integer"},
                    "path": {"type": "string"},
                    "entries": {"type": "array", "items": {"type": "object"}},
                    "count": {"type": "integer"},
                    "truncated": {"type": "boolean"},
                },
            },
            "examples": [
                {"description": "List workspace root", "body": {"path": "/workspace"}},
                {"description": "List userfile", "body": {"path": "/userfile"}},
                {"description": "List subdirectory", "body": {"path": "/workspace/src"}},
            ],
            "timeout_seconds": 30,
            "security": {
                "allowed_roots": ["/workspace", "/userfile"],
                "symlink_protection": True,
                "max_entries": _env_int("MAX_DIR_ENTRIES", 1000),
                "mutation_allowed": False,
            },
            "limits": common_limits,
            "retry_safe": True,
            "notes": "Structured alternative to 'ls'. Returns JSON, not shell text.",
        },
        {
            "name": "file/read",
            "method": "POST",
            "path": "/file/read",
            "description": "Read a file's content as structured JSON.",
            "when_to_use": "Read text files (source code, configs, logs, data). Returns content with size and truncation info. Always prefer this over /command with 'cat'.",
            "when_not_to_use": "When you need to list directory (use /file/list), search for files (use /file/search), or process binary files (use /command).",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path to read"}
                },
                "required": ["path"],
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "status": {"type": "integer"},
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                    "size": {"type": "integer"},
                    "truncated": {"type": "boolean"},
                },
            },
            "examples": [
                {"description": "Read a Python file", "body": {"path": "/workspace/main.py"}},
                {"description": "Read a config", "body": {"path": "/workspace/config.json"}},
                {"description": "Read from userfile", "body": {"path": "/userfile/data.csv"}},
            ],
            "timeout_seconds": 30,
            "security": {
                "allowed_roots": ["/workspace", "/userfile"],
                "symlink_protection": True,
                "binary_detection": True,
                "mutation_allowed": False,
            },
            "limits": common_limits,
            "retry_safe": True,
            "notes": "Structured alternative to 'cat'. Returns JSON with content, size, and truncation status.",
        },
        {
            "name": "file/search",
            "method": "POST",
            "path": "/file/search",
            "description": "Search for files using glob patterns.",
            "when_to_use": "Find files by name pattern (e.g., *.py, test_*). Returns matching paths. Always prefer this over /command with 'find'.",
            "when_not_to_use": "When you need to read file contents (use /file/read), list a specific directory (use /file/list), or search file contents (use /command with 'grep').",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Root directory to search", "default": "/workspace"},
                    "pattern": {"type": "string", "description": "Glob pattern (e.g., *.py, test_*)", "default": "*"},
                    "type": {"type": "string", "enum": ["file", "dir", "all"], "description": "Filter by type", "default": "file"},
                },
                "required": ["pattern"],
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "status": {"type": "integer"},
                    "path": {"type": "string"},
                    "pattern": {"type": "string"},
                    "matches": {"type": "array", "items": {"type": "string"}},
                    "count": {"type": "integer"},
                    "truncated": {"type": "boolean"},
                },
            },
            "examples": [
                {"description": "Find all Python files", "body": {"path": "/workspace", "pattern": "*.py", "type": "file"}},
                {"description": "Find test files", "body": {"path": "/workspace", "pattern": "test_*", "type": "file"}},
                {"description": "Find all directories", "body": {"path": "/workspace", "pattern": "*", "type": "dir"}},
            ],
            "timeout_seconds": 30,
            "security": {
                "allowed_roots": ["/workspace", "/userfile"],
                "symlink_protection": True,
                "max_results": _env_int("MAX_SEARCH_RESULTS", 500),
                "max_depth": _env_int("MAX_SEARCH_DEPTH", 10),
                "mutation_allowed": False,
            },
            "limits": common_limits,
            "retry_safe": True,
            "notes": "Structured alternative to 'find'. Returns JSON array of matching paths.",
        },
        {
            "name": "file/metadata",
            "method": "POST",
            "path": "/file/metadata",
            "description": "Get file or directory metadata.",
            "when_to_use": "Check if a file exists, get its size, permissions, modification time. Always prefer this over /command with 'stat'.",
            "when_not_to_use": "When you need to read file contents (use /file/read), list directory (use /file/list), or execute shell commands (use /command).",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File or directory path"}
                },
                "required": ["path"],
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "status": {"type": "integer"},
                    "name": {"type": "string"},
                    "path": {"type": "string"},
                    "size": {"type": "integer"},
                    "modified": {"type": "string"},
                    "permissions": {"type": "string"},
                    "is_dir": {"type": "boolean"},
                    "is_file": {"type": "boolean"},
                    "is_symlink": {"type": "boolean"},
                },
            },
            "examples": [
                {"description": "Check file metadata", "body": {"path": "/workspace/main.py"}},
                {"description": "Check directory", "body": {"path": "/workspace/src"}},
                {"description": "Check if file exists", "body": {"path": "/workspace/config.json"}},
            ],
            "timeout_seconds": 30,
            "security": {
                "allowed_roots": ["/workspace", "/userfile"],
                "symlink_protection": True,
                "mutation_allowed": False,
            },
            "limits": common_limits,
            "retry_safe": True,
            "notes": "Structured alternative to 'stat'. Returns JSON with file info.",
        },
        {
            "name": "system/info",
            "method": "GET",
            "path": "/system/info",
            "description": "Get system information (OS, CPU, memory, disk).",
            "when_to_use": "Understand the runtime environment before executing commands. Always prefer this over /command with 'uname', 'free', 'df'.",
            "when_not_to_use": "When you need to inspect host /proc (use /proc), or execute shell commands (use /command).",
            "input_schema": None,
            "output_schema": {
                "type": "object",
                "properties": {
                    "status": {"type": "integer"},
                    "os": {"type": "string"},
                    "arch": {"type": "string"},
                    "cpu_count": {"type": "integer"},
                    "memory_total_mb": {"type": "integer"},
                    "memory_available_mb": {"type": "integer"},
                    "disk_total_gb": {"type": "number"},
                    "disk_free_gb": {"type": "number"},
                    "container": {"type": "boolean"},
                },
            },
            "security": {
                "read_only": True,
                "no_secrets": True,
                "mutation_allowed": False,
            },
            "limits": common_limits,
            "retry_safe": True,
            "notes": "Structured alternative to 'uname -a && free -m && df -h'. Returns JSON.",
        },

        # === Shell / Command Tools (v0.4.x) ===
        {
            "name": "command",
            "method": "POST",
            "path": "/command",
            "description": "Execute a shell command inside the Tool Server container.",
            "when_to_use": "Run commands that are NOT file listing (use /file/list), file reading (use /file/read), file searching (use /file/search), file metadata (use /file/metadata), or system info (use /system/info). Use for: scripts, git, npm, pip, compilation, testing, build tools, and any complex shell operations.",
            "when_not_to_use": "When a structured tool exists for the task. Structured tools return JSON and don't require shell syntax.",
            "input_schema": {
                "type": "string",
                "description": "Shell command to execute",
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "status": {"type": "integer"},
                    "output": {"type": "string"},
                    "exit_code": {"type": "integer"},
                },
            },
            "examples": [
                {"description": "Run a script", "body": "bash /workspace/script.sh"},
                {"description": "Git operations", "body": "cd /workspace && git status"},
                {"description": "Install dependencies", "body": "pip install -r requirements.txt"},
            ],
            "timeout_seconds": _env_int('COMMAND_TIMEOUT', 30),
            "security": {
                "blocked_commands": blocked,
                "note": "rm is always blocked. Other commands blocked via BLOCK env.",
                "mutation_allowed": False,
            },
            "limits": common_limits,
            "retry_safe": True,
            "notes": "General-purpose shell execution. Use structured tools when available.",
        },
        {
            "name": "file",
            "method": "POST",
            "path": "/file",
            "description": "Alias for /command. Executes shell commands with the same policy.",
            "when_not_to_use": "Prefer /command for clarity. This is kept for backward compatibility only.",
            "input_schema": {"type": "string"},
            "output_schema": {
                "type": "object",
                "properties": {
                    "status": {"type": "integer"},
                    "output": {"type": "string"},
                    "exit_code": {"type": "integer"},
                },
            },
            "timeout_seconds": _env_int('COMMAND_TIMEOUT', 30),
            "security": {
                "blocked_commands": blocked,
                "mutation_allowed": False,
            },
            "limits": common_limits,
            "retry_safe": True,
            "notes": "Alias for /command. Prefer /command or structured tools.",
        },
        {
            "name": "filepc",
            "method": "POST",
            "path": "/filepc",
            "description": "Execute file operations inside a disposable, isolated container with access to a host directory.",
            "when_to_use": "Safely operate on files in the host directory mapped to /userfile. Network is disabled, filesystem is read-only.",
            "when_not_to_use": "When you only need to read files (use /file/read) or list directories (use /file/list).",
            "input_schema": {"type": "string"},
            "output_schema": {
                "type": "object",
                "properties": {
                    "status": {"type": "integer"},
                    "output": {"type": "string"},
                    "exit_code": {"type": "integer"},
                },
            },
            "examples": [
                {"description": "Read a file", "body": "cat /userfile/config.json"},
                {"description": "List directory", "body": "ls -la /userfile"},
            ],
            "timeout_seconds": _env_int('FILEPC_TIMEOUT', 120),
            "security": {
                "blocked_commands": blocked,
                "network": "none",
                "filesystem": "read-only",
                "capabilities": "dropped",
                "mutation_allowed": False,
            },
            "limits": common_limits,
            "retry_safe": True,
            "notes": "Isolated container for host file access. More restricted than /command.",
        },
        {
            "name": "commandpc",
            "method": "POST",
            "path": "/commandpc",
            "description": "Execute a command on a remote host via SSH.",
            "when_to_use": "Run commands on the configured SSH host (e.g., the host machine). Requires SSH key configuration.",
            "input_schema": {"type": "string"},
            "output_schema": {
                "type": "object",
                "properties": {
                    "status": {"type": "integer"},
                    "output": {"type": "string"},
                    "exit_code": {"type": "integer"},
                },
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
            "notes": "Remote command execution via SSH. Each invocation creates a new connection.",
        },
        {
            "name": "proc",
            "method": "POST",
            "path": "/proc",
            "description": "Read-only inspection of host /proc filesystem (CPU, memory, processes).",
            "when_to_use": "Check host system status: CPU info, memory usage, process list, uptime, etc.",
            "when_not_to_use": "When you only need container info (use /system/info).",
            "input_schema": {"type": "string"},
            "output_schema": {
                "type": "object",
                "properties": {
                    "status": {"type": "integer"},
                    "output": {"type": "string"},
                    "exit_code": {"type": "integer"},
                },
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
            "input_schema": {"type": "string"},
            "output_schema": {
                "type": "object",
                "properties": {
                    "status": {"type": "integer"},
                    "output": {"type": "string"},
                    "exit_code": {"type": "integer"},
                },
            },
            "examples": [
                {"description": "List running containers", "body": "docker ps"},
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
            "input_schema": {"type": "string", "description": "URL to download"},
            "output_schema": {
                "type": "object",
                "properties": {
                    "status": {"type": "integer"},
                    "output": {"type": "string"},
                },
            },
            "examples": [
                {"description": "Download a CSV", "body": "https://example.com/data.csv"},
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
            "input_schema": None,
            "output_schema": {
                "type": "object",
                "properties": {
                    "status": {"type": "integer"},
                    "variables": {"type": "object"},
                },
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
            "input_schema": None,
            "output_schema": {
                "type": "object",
                "properties": {
                    "status": {"type": "integer"},
                    "requests": {"type": "integer"},
                    "tool_calls": {"type": "integer"},
                    "errors": {"type": "integer"},
                    "rate_limited": {"type": "integer"},
                    "uptime_seconds": {"type": "number"},
                },
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
            "input_schema": None,
            "output_schema": {
                "type": "object",
                "properties": {
                    "status": {"type": "string"},
                    "version": {"type": "string"},
                },
            },
            "retry_safe": True,
            "notes": "No authentication required. Useful for connectivity checks.",
        },
    ]


@router.get("/tools")
async def tools(authorization: str | None = Header(None)):
    auth(authorization)
    return {
        "version": os.getenv("APP_VERSION", "0.0.5"),
        "tools": _tool_defs(),
        "global_limits": {
            "rate_limit": f"{_env_int('RATE_LIMIT_REQUESTS', 30)} requests per {_env_int('RATE_LIMIT_WINDOW', 60)} seconds",
            "max_concurrent_tools": _env_int('MAX_CONCURRENT_TOOLS', 4),
            "max_body_bytes": _env_int('MAX_BODY_BYTES', 65536),
            "max_output_bytes": output_limit(),
            "per_task_call_limit": _env_int('MAX_TOOL_CALLS', 20),
        },
        "allowed_roots": ["/workspace", "/userfile"],
        "authentication": {
            "type": "Bearer token",
            "header": "Authorization: Bearer <API_KEY>",
        },
        "error_format": {
            "success": {"status": 200},
            "command_failed": {"status": 200, "output": "string", "exit_code": "int"},
            "client_error": {"status": "4xx", "error": "string", "message": "string"},
            "rate_limited": {"status": 429, "output": "string", "Retry-After": "int"},
            "timeout": {"detail": "string"},
        },
        "tool_selection_guide": {
            "list_files": "Use /file/list, not /command with 'ls'",
            "read_file": "Use /file/read, not /command with 'cat'",
            "search_files": "Use /file/search, not /command with 'find'",
            "file_metadata": "Use /file/metadata, not /command with 'stat'",
            "system_info": "Use /system/info, not /command with 'uname/free/df'",
            "complex_operations": "Use /command for scripts, git, npm, build tools, and any operation that requires shell features",
        },
    }
