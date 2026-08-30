from __future__ import annotations

from collections import defaultdict, deque
import asyncio
import os
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.api.command import router as command_router
from app.api.file import router as file_router
from app.api.filepc import router as filepc_router
from app.api.docker import router as docker_router
from app.api.getfile import router as getfile_router
from app.api.commandpc import router as commandpc_router
from app.api.proc import router as proc_router
from app.api.help import router as help_router
from app.api.env import router as env_router
from app.api.health import router as health_router
from app.api.stats import router as stats_router
from app.api.tools import router as tools_router
from app import stats

app = FastAPI(
    title="AI Agent Tool Server",
    version=os.getenv("APP_VERSION", "0.0.4"),
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

RATE_LIMIT_REQUESTS = max(1, int(os.getenv("RATE_LIMIT_REQUESTS", "30")))
RATE_LIMIT_WINDOW = max(1, int(os.getenv("RATE_LIMIT_WINDOW", "60")))
MAX_BODY_BYTES = max(1024, int(os.getenv("MAX_BODY_BYTES", "65536")))
MAX_CONCURRENT = max(1, int(os.getenv("MAX_CONCURRENT_TOOLS", "4")))

_hits = defaultdict(deque)
_rate_lock = asyncio.Lock()
_tool_semaphore = asyncio.Semaphore(MAX_CONCURRENT)
_task_counts = defaultdict(int)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
_index_html: str | None = None

# API endpoints that require rate limiting.
# SPA routes, static files, /health, /help are excluded.
_API_RATE_LIMIT_PATHS = frozenset({
    "/command", "/file", "/filepc", "/commandpc",
    "/proc", "/docker", "/getfile", "/stats", "/env",
})


def _get_index_html() -> str:
    global _index_html
    if _index_html is None:
        index_path = os.path.join(STATIC_DIR, "index.html")
        if os.path.isfile(index_path):
            with open(index_path) as f:
                _index_html = f.read()
        else:
            _index_html = "<html><body><h1>Web Console not built</h1></body></html>"
    return _index_html


@app.middleware("http")
async def guard(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
    request.state.request_id = request_id
    path = request.url.path

    # Static files, /health, /help: skip all checks.
    if path.startswith("/static") or path in {"/help", "/health", "/tools"}:
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    # Non-API paths (SPA routes, frontend traffic): skip rate limit and
    # body size checks, but still apply concurrency limit.
    if path not in _API_RATE_LIMIT_PATHS:
        async with _tool_semaphore:
            response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    # API endpoints: full protection (rate limit + body size + concurrency).
    key = request.headers.get("authorization") or (request.client.host if request.client else "unknown")
    task_id = request.headers.get("X-Agent-Task-ID")
    now = time.monotonic()
    async with _rate_lock:
        q = _hits[key]
        while q and now - q[0] > RATE_LIMIT_WINDOW:
            q.popleft()
        if len(q) >= RATE_LIMIT_REQUESTS:
            stats.rate_limited()
            response = JSONResponse(
                status_code=429,
                content={"status": 429, "output": "Rate limit exceeded. Try again later.", "request_id": request_id},
                headers={"Retry-After": str(RATE_LIMIT_WINDOW)},
            )
            response.headers["X-Request-ID"] = request_id
            return response
        q.append(now)

        if task_id:
            task_key = f"{key}:{task_id}"
            if _task_counts[task_key] >= max(1, int(os.getenv("MAX_TOOL_CALLS", "20"))):
                response = JSONResponse(
                    status_code=429,
                    content={
                        "status": 429,
                        "output": "Maximum tool calls for this task reached.",
                        "request_id": request_id,
                        "task_id": task_id,
                    },
                    headers={"Retry-After": str(RATE_LIMIT_WINDOW)},
                )
                response.headers["X-Request-ID"] = request_id
                return response
            _task_counts[task_key] += 1

    length = request.headers.get("content-length")
    if length:
        try:
            if int(length) > MAX_BODY_BYTES:
                response = JSONResponse(status_code=413, content={"status": 413, "output": "Request body too large.", "request_id": request_id})
                response.headers["X-Request-ID"] = request_id
                return response
        except ValueError:
            pass

    if request.method in {"POST", "PUT", "PATCH"} and not length:
        body = await request.body()
        if len(body) > MAX_BODY_BYTES:
            response = JSONResponse(status_code=413, content={"status": 413, "output": "Request body too large.", "request_id": request_id})
            response.headers["X-Request-ID"] = request_id
            return response
        request._receive = lambda: {"type": "http.request", "body": body, "more_body": False}

    async with _tool_semaphore:
        stats.tool_call()
        response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    stats.request(response.status_code)
    return response


# API routes — registered first, highest priority.
for r in [
    command_router, file_router, filepc_router, docker_router,
    getfile_router, commandpc_router, proc_router, help_router,
    env_router, health_router, stats_router, tools_router,
]:
    app.include_router(r)

# Static files — serves /app/static for /static/* paths.
if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# Explicit 404 for disabled docs endpoints.
@app.get("/docs")
@app.get("/redoc")
@app.get("/openapi.json")
async def docs_disabled():
    return JSONResponse(status_code=404, content={"detail": "Not found"})


# SPA fallback — catch-all AFTER api + static.
# Serves index.html for any path not matched above.
@app.get("/{full_path:path}", response_class=HTMLResponse)
async def spa_fallback(full_path: str):
    return HTMLResponse(content=_get_index_html())
