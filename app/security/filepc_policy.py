from __future__ import annotations

import re
import shlex

# /filepc is intentionally conservative: commands must operate from /userfile
# and cannot explicitly address paths outside that tree.
FORBIDDEN = re.compile(r"(?:^|[\s;&|(){}<>])(?:cd|chroot|mount|umount|nsenter|unshare)(?:[\s;&|(){}<>]|$)", re.I)


def check_filepc(command: str) -> tuple[bool, str | None]:
    if not command or len(command) > 32768:
        return False, "invalid or oversized command"
    if FORBIDDEN.search(command):
        return False, "filesystem namespace operation is forbidden"
    if any(x in command for x in ("\x00", "\n\r")):
        return False, "invalid command"
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError:
        return False, "invalid shell syntax"
    for token in tokens:
        # Explicit absolute paths must be under /userfile. Relative traversal
        # is rejected because the working directory is /userfile.
        if token.startswith("/") and not token.startswith("/userfile"):
            return False, "path outside /userfile"
        if token == ".." or token.startswith("../") or "/../" in token:
            return False, "path traversal outside /userfile"
    return True, None
