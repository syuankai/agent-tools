from pathlib import Path
def safe_userfile(path:str)->Path:
    root=Path("/userfile").resolve()
    p=Path(path)
    if not p.is_absolute(): p=root/p
    resolved=p.resolve(strict=False)
    if resolved!=root and root not in resolved.parents:
        raise PermissionError("Path outside /userfile")
    return resolved
