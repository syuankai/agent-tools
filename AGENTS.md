# AGENTS.md

## Project Overview

AI Agent Tool Server — a FastAPI HTTP tool server for AI agents, packaged in a single Docker image with a React (Vite) web console.

- **Runtime**: Python 3.12 + FastAPI + uvicorn
- **Frontend**: React + TypeScript + Vite (built into `/app/static/`)
- **Container**: Ubuntu 24.04, no Node.js in runtime image
- **Version**: v0.5.0 (structured file tools)

## Quick Commands

### Build
```bash
./build.sh                    # Builds docker image agent-tools:v0.5.0
```

### Python (no test suite exists)
```bash
python3 -m compileall app     # Compile check — must pass with 0 errors
```

### WebCon frontend
```bash
cd webcon && npm ci && npm run build   # TypeScript + Vite build
cd webcon && npm run lint              # oxlint
```

### Docker smoke test
```bash
docker run -d --name test -p 8081:8080 -e API_KEY=test123 agent-tools:v0.5.0
curl -s http://localhost:8081/health
curl -s -H "Authorization: Bearer test123" http://localhost:8081/tools
docker rm -f test
```

There is **no test suite**. Verification is: `compileall` → `npm run build` → `docker build` → manual smoke test.

## Architecture

```
app/
  main.py              # FastAPI app, middleware (rate limit, body size, concurrency)
  stats.py             # In-memory request counters
  api/
    command.py         # POST /command — shell in container
    file.py            # POST /file — alias for /command
    filepc.py          # POST /filepc — isolated container with host dir
    commandpc.py       # POST /commandpc — SSH to remote host
    proc.py            # POST /proc — read-only /proc inspection
    docker.py          # POST /docker — Docker socket commands
    getfile.py         # POST /getfile — download URL with SSRF protection
    file_list.py       # POST /file/list — structured directory listing
    file_read.py       # POST /file/read — structured file reading
    file_search.py     # POST /file/search — glob-based file search
    file_metadata.py   # POST /file/metadata — file info
    system_info.py     # GET /system/info — OS/CPU/memory/disk
    env.py             # GET /env — allowlisted env vars
    stats.py           # GET /stats — request counters
    health.py          # GET /health — unauthenticated
    help.py            # GET /help — human-readable docs
    tools.py           # GET /tools — Agent auto-discovery catalog
  security/
    common.py          # auth(), result(), trim_output(), output_limit()
    command_policy.py  # Blocklist-based command validation
    filepc_policy.py   # /filepc path restrictions
    proc_policy.py     # /proc allowlist
    path_policy.py     # Structured file tool path validation (NEW v0.5.0)
```

## Key Security Details

- **path_policy.py** is the core security component for structured file tools. Uses `os.path.realpath()` with prefix-collision-safe root checks. All `/file/*` endpoints depend on it.
- **command_policy.py** uses regex-based blocklist. `rm` is permanently blocked. Custom blocks via `BLOCK` env var.
- **ALLOWED_ROOTS** for file tools: `/workspace`, `/userfile`. Symlinks that escape these roots are rejected.
- Binary detection in `/file/read` is heuristic (null bytes + non-printable ratio + UTF-8 decode), not just null-byte check.
- Docker mutation guard blocks `run`, `create`, `stop`, `rm`, `compose`, etc. by default.

## Rate Limiting

API endpoints are rate-limited. SPA routes, `/health`, `/help`, `/tools` are excluded.

`_API_RATE_LIMIT_PATHS` in `main.py` must include any new API endpoint.

## Build Context

`build.sh` copies to `/tmp/agent-tools-build-ctx/` to avoid space-in-path Docker issues. The Dockerfile is multi-stage: `webcon-builder` (Node 22) → runtime (Ubuntu 24.04, no nodejs).

## Conventions

- All POST endpoints accept `Body(...)` (not query params) with `Content-Type: text/plain` or `application/json`.
- Response format: `{"status": 200, ...}` for success. Errors use `{"detail": {"status": N, "error": "...", "message": "..."}}` for new endpoints, or FastAPI's default `{"detail": "..."}` for legacy endpoints.
- `result()` in `common.py` always returns HTTP 200 with `exit_code` field for command failures (not HTTP 500).
- WebCon client.ts sends `Content-Type: text/plain` for POST bodies. New structured endpoints use `application/json`.

## Version Tagging

Version is defined in: `build.sh` (docker tag), `docker-compose.yml` (image + APP_VERSION), `main.py` (FastAPI version), `help.py`, `tools.py`. Update all when bumping version.

## Do Not

- Do not commit `__pycache__/`, `webcon/dist/`, `webcon/node_modules/`
- Do not modify existing v0.4.x endpoint contracts
- Do not refactor existing security policies unless explicitly asked
- Do not add features not in the current scope
