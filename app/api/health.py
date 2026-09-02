from fastapi import APIRouter
import os

router = APIRouter()

@router.get("/health")
async def health():
    return {"status": "ok", "version": os.getenv("APP_VERSION", "0.0.5")}
