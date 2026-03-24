from fastapi import FastAPI

from app.api.v1.api import api_router
from app.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
)


@app.get("/", tags=["default"])
def root():
    return {"message": "Husky Tracking API is running"}


app.include_router(api_router, prefix=settings.API_V1_PREFIX)