from __future__ import annotations

import os
import re
from fastapi import APIRouter, Header, HTTPException
from app.security.common import auth

router = APIRouter()


def _csv(name: str) -> set[str]:
    return {x.strip() for x in os.getenv(name, "").split(",") if x.strip()}


def _is_secret(name: str) -> bool:
    patterns = _csv("ENV_REDACT_PATTERNS") or {"KEY", "TOKEN", "PASSWORD", "SECRET", "CREDENTIAL"}
    upper = name.upper()
    return any(re.search(p, upper, re.I) for p in patterns)


@router.get("/env")
async def env(authorization: str | None = Header(None)):
    auth(authorization)
    allow = _csv("ENV_ALLOWLIST")
    deny = _csv("ENV_DENYLIST")
    redact = os.getenv("ENV_REDACT", "true").lower() in {"1", "true", "yes", "on"}
    if not allow:
        return {"status": 200, "variables": {}}

    variables = {}
    for name in sorted(allow):
        if name in deny or name not in os.environ:
            continue
        variables[name] = "[REDACTED]" if redact and _is_secret(name) else os.environ[name]
    return {"status": 200, "variables": variables}
