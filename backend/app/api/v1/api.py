from fastapi import APIRouter

from app.api.v1.endpoints import dogs, health, imports, worklogs

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(dogs.router, prefix="/dogs", tags=["dogs"])
api_router.include_router(worklogs.router, prefix="/worklogs", tags=["worklogs"])
api_router.include_router(imports.router, tags=["import"])