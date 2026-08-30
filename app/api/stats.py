from fastapi import APIRouter, Header
from app.security.common import auth
from app.stats import snapshot

router = APIRouter()

@router.get("/stats")
async def stats(authorization: str | None = Header(None)):
    auth(authorization)
    return {"status": 200, **snapshot()}
