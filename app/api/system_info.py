"""GET /system/info — System information as structured JSON."""

from __future__ import annotations

import os
import platform

from fastapi import APIRouter, Header

from app.security.common import auth

router = APIRouter()


def _read_proc_file(path: str) -> str | None:
    """Read a /proc file if available."""
    try:
        with open(path) as f:
            return f.read().strip()
    except (OSError, IOError):
        return None


def _get_memory_info() -> dict:
    """Get memory info from /proc/meminfo."""
    content = _read_proc_file("/proc/meminfo")
    if not content:
        return {"total_mb": 0, "available_mb": 0}

    info = {}
    for line in content.splitlines():
        parts = line.split(":")
        if len(parts) == 2:
            key = parts[0].strip()
            val = parts[1].strip()
            # Parse kB values to MB
            if val.endswith(" kB"):
                val = val[:-3]
                try:
                    info[key] = int(val) // 1024
                except ValueError:
                    pass

    return {
        "total_mb": info.get("MemTotal", 0),
        "available_mb": info.get("MemAvailable", 0),
        "free_mb": info.get("MemFree", 0),
        "buffers_mb": info.get("Buffers", 0),
        "cached_mb": info.get("Cached", 0),
    }


def _get_disk_info(path: str = "/") -> dict:
    """Get disk usage info using os.statvfs."""
    try:
        st = os.statvfs(path)
        block_size = st.f_frsize
        return {
            "total_gb": round((st.f_blocks * block_size) / (1024 ** 3), 2),
            "free_gb": round((st.f_bavail * block_size) / (1024 ** 3), 2),
            "used_gb": round(((st.f_blocks - st.f_bavail) * block_size) / (1024 ** 3), 2),
        }
    except OSError:
        return {"total_gb": 0, "free_gb": 0, "used_gb": 0}


def _get_cpu_count() -> int:
    """Get CPU count from os.cpu_count() or /proc/cpuinfo."""
    count = os.cpu_count()
    if count:
        return count

    content = _read_proc_file("/proc/cpuinfo")
    if content:
        return content.count("processor")

    return 0


def _is_container() -> bool:
    """Detect if running inside a container."""
    # Check for /.dockerenv (Docker)
    if os.path.exists("/.dockerenv"):
        return True
    # Check cgroup (Docker, podman, kubernetes)
    cgroup = _read_proc_file("/proc/1/cgroup")
    if cgroup and ("docker" in cgroup or "containerd" in cgroup or "kubepods" in cgroup):
        return True
    return False


@router.get("/system/info")
async def system_info(authorization: str | None = Header(None)):
    auth(authorization)

    uname = platform.uname()
    mem = _get_memory_info()
    disk = _get_disk_info()

    return {
        "status": 200,
        "os": uname.system.lower(),
        "os_release": uname.release,
        "arch": platform.machine(),
        "hostname": uname.node,
        "python_version": platform.python_version(),
        "cpu_count": _get_cpu_count(),
        "memory_total_mb": mem["total_mb"],
        "memory_available_mb": mem["available_mb"],
        "memory_free_mb": mem["free_mb"],
        "memory_buffers_mb": mem["buffers_mb"],
        "memory_cached_mb": mem["cached_mb"],
        "disk_total_gb": disk["total_gb"],
        "disk_free_gb": disk["free_gb"],
        "disk_used_gb": disk["used_gb"],
        "container": _is_container(),
        "pid": os.getpid(),
    }
