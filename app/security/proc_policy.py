import re
import shlex

ALLOWED = {
    "cat", "ls", "head", "tail", "grep", "rg", "sort", "wc", "cut",
    "tr", "stat", "readlink", "realpath", "pwd", "find", "sed"
}
# Operations that can execute commands, modify files, or make find perform
# actions are forbidden.
BAD_TOKEN = re.compile(
    r"(^|[-/])(?:exec(?:dir)?|delete|ok(?:dir)?|write|inplace)$|"
    r"^(?:-i|-I|--in-place|--debug|--sandbox)$",
    re.I,
)

def _segment_ok(segment: str) -> bool:
    try:
        argv = shlex.split(segment)
    except ValueError:
        return False
    if not argv or argv[0] not in ALLOWED:
        return False
    for token in argv:
        if BAD_TOKEN.search(token):
            return False
        # Prevent shell/path tricks and commands that can open arbitrary host
        # files. All explicit absolute paths must stay under /hostproc.
        if token.startswith("/") and not token.startswith("/hostproc"):
            return False
        if any(x in token for x in (";", "&&", "||", "`", "$(", ">", "<")):
            return False
    return True

def check_proc(command: str) -> bool:
    if not command or len(command) > 8192:
        return False
    # Only pipelines are accepted as shell syntax.
    if any(x in command for x in (";", "&&", "||", "&", ">", "<", "`")):
        return False
    parts = [p.strip() for p in command.split("|")]
    return bool(parts) and all(_segment_ok(p) for p in parts)
