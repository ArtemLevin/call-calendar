from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.endpoints.bookings import router as bookings_router
from app.api.endpoints.colleagues import router as colleagues_router
from app.api.endpoints.meeting_settings import router as meeting_settings_router

app = FastAPI(title="Call Calendar API")
app.include_router(bookings_router)
app.include_router(meeting_settings_router)
app.include_router(colleagues_router)
app.mount("/web", StaticFiles(directory="web"), name="web")


@app.get("/")
async def frontend() -> FileResponse:
    # Why: exposing a stable root UI entrypoint enables manual end-to-end checks
    # of booking flows without coupling frontend rollout to additional infrastructure.
    return FileResponse("web/index.html")


@app.get("/health")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
