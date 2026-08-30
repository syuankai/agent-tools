from __future__ import annotations

import threading
import time
from collections import Counter

_started = time.time()
_lock = threading.Lock()
_requests = 0
_tool_calls = 0
_errors = 0
_rate_limited = 0
_statuses = Counter()


def request(status: int) -> None:
    global _requests, _errors
    with _lock:
        _requests += 1
        _statuses[status] += 1
        if status >= 400:
            _errors += 1


def tool_call() -> None:
    global _tool_calls
    with _lock:
        _tool_calls += 1


def rate_limited() -> None:
    global _rate_limited
    with _lock:
        _rate_limited += 1


def snapshot() -> dict:
    with _lock:
        return {
            "requests": _requests,
            "tool_calls": _tool_calls,
            "errors": _errors,
            "rate_limited": _rate_limited,
            "uptime_seconds": round(time.time() - _started, 1),
            "statuses": dict(_statuses),
        }
