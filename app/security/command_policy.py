"""Command safety policy shared by command-capable endpoints."""

from __future__ import annotations

import os
import re
import shlex

# rm is permanently blocked and cannot be removed through BLOCK.
SYSTEM_BLOCKED = {"rm"}


def _configured_blocked() -> set[str]:
    raw = os.getenv("BLOCK", "")
    return {
        item.strip().lower()
        for item in raw.split(",")
        if item.strip()
    }


def blocked_commands() -> set[str]:
    return SYSTEM_BLOCKED | _configured_blocked()


def _basename(token: str) -> str:
    token = token.strip().strip("'\"")
    token = token.rsplit("/", 1)[-1]
    return token.lower()


def _contains_blocked_word(command: str, blocked: set[str]) -> str | None:
    # This catches commands appearing after shell operators and inside common
    # shell snippets (e.g. "bash -c 'rm -f x'"). It intentionally errs on
    # the side of blocking rather than allowing an ambiguous bypass.
    for name in sorted(blocked, key=len, reverse=True):
        pattern = rf"(?<![A-Za-z0-9_.-])(?:/[^\s;&|()<>`$]+/)?{re.escape(name)}(?![A-Za-z0-9_.-])"
        if re.search(pattern, command, re.IGNORECASE):
            return name
    return None


def check_command(command: str) -> tuple[bool, str | None]:
    if not command or len(command) > 32768:
        return False, "invalid or oversized command"

    blocked = blocked_commands()
    hit = _contains_blocked_word(command, blocked)
    if hit:
        return False, hit

    try:
        tokens = shlex.split(command, posix=True)
    except ValueError:
        return False, "invalid shell syntax"

    for token in tokens:
        base = _basename(token)
        if base in blocked:
            return False, base

    return True, None


def check_command_bool(command: str) -> bool:
    return check_command(command)[0]
