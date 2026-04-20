from fastapi import APIRouter

from app.api.v1.endpoints.analytics import router as analytics_router
from app.api.v1.endpoints.dashboard import router as dashboard_router
from app.api.v1.endpoints.dogs import router as dogs_router
from app.api.v1.endpoints.exports import router as exports_router
from app.api.v1.endpoints.imports import router as imports_router
from app.api.v1.endpoints.team_builder import router as team_builder_router
from app.api.v1.endpoints.worklog_entry import router as worklog_entry_router
from app.api.v1.endpoints.worklogs import router as worklogs_router

api_router = APIRouter()
api_router.include_router(imports_router, tags=["import"])
api_router.include_router(dogs_router, prefix="/dogs", tags=["dogs"])
api_router.include_router(worklogs_router, prefix="/worklogs", tags=["worklogs"])
api_router.include_router(worklog_entry_router)
api_router.include_router(dashboard_router)
api_router.include_router(analytics_router)
api_router.include_router(exports_router)
api_router.include_router(team_builder_router)