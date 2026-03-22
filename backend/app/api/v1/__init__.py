from fastapi import APIRouter

from app.api.v1.assets import router as assets_router

router = APIRouter(prefix="/api/v1")
router.include_router(assets_router)
