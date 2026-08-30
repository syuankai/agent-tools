from __future__ import annotations

from fastapi import APIRouter, Body, Header, HTTPException
import ipaddress
import os
import re
import socket
import tempfile
from urllib.parse import urlparse

import httpx

from app.security.common import auth, result

router = APIRouter()
SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]")
MAX_FILE_SIZE = max(1, int(os.getenv("MAX_FILE_SIZE", "104857600")))
DOWNLOAD_TIMEOUT = float(os.getenv("DOWNLOAD_TIMEOUT", "300"))


def _blocked_ip(value: str) -> bool:
    ip = ipaddress.ip_address(value)
    return (
        ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved
        or ip.is_multicast or ip.is_unspecified
    )


def _resolve_public(host: str, port: int) -> None:
    try:
        infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise HTTPException(400, f"Unable to resolve download host: {exc}")
    if not infos:
        raise HTTPException(400, "Unable to resolve download host.")
    for info in infos:
        addr = info[4][0]
        try:
            if _blocked_ip(addr):
                raise HTTPException(403, "Downloads to private/internal addresses are forbidden.")
        except ValueError:
            raise HTTPException(400, "Invalid resolved address.")


@router.post("/getfile")
async def getfile(body: str = Body(...), authorization: str | None = Header(None)):
    auth(authorization)
    url = body.strip()
    u = urlparse(url)
    if u.scheme not in ("http", "https") or not u.hostname:
        raise HTTPException(400, "Only HTTP/HTTPS URLs are allowed.")

    port = u.port or (443 if u.scheme == "https" else 80)
    _resolve_public(u.hostname, port)

    name = os.path.basename(u.path) or "download"
    name = SAFE_NAME.sub("_", name)[:200]
    if name in (".", "..", ""):
        name = "download"
    dest = f"/aifile/{name}"
    fd, tmp = tempfile.mkstemp(prefix=".download-", dir="/aifile")
    os.close(fd)

    timeout = httpx.Timeout(DOWNLOAD_TIMEOUT, connect=15.0)
    total = 0
    current_url = url
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
            for _ in range(5):
                parsed = urlparse(current_url)
                if parsed.scheme not in ("http", "https") or not parsed.hostname:
                    raise HTTPException(400, "Redirect target is not HTTP/HTTPS.")
                current_port = parsed.port or (443 if parsed.scheme == "https" else 80)
                _resolve_public(parsed.hostname, current_port)
                response = await client.stream("GET", current_url, follow_redirects=False).__aenter__()
                try:
                    if response.status_code in {301, 302, 303, 307, 308}:
                        location = response.headers.get("location")
                        if not location:
                            raise HTTPException(502, "Redirect without a Location header.")
                        current_url = str(response.url.join(location))
                        continue
                    response.raise_for_status()
                    content_length = response.headers.get("content-length")
                    if content_length and int(content_length) > MAX_FILE_SIZE:
                        raise HTTPException(413, "Downloaded file is too large.")
                    with open(tmp, "wb") as out:
                        async for chunk in response.aiter_bytes(65536):
                            total += len(chunk)
                            if total > MAX_FILE_SIZE:
                                raise HTTPException(413, "Downloaded file is too large.")
                            out.write(chunk)
                    os.replace(tmp, dest)
                    return result(f"Downloaded: {dest}")
                finally:
                    await response.aclose()
            raise HTTPException(502, "Too many redirects.")
    except HTTPException:
        raise
    except httpx.TimeoutException:
        raise HTTPException(504, "Download timed out.")
    except httpx.HTTPError as exc:
        raise HTTPException(502, f"Download failed: {exc}")
    finally:
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass
