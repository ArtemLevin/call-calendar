from fastapi import FastAPI

from app.api.endpoints.bookings import router as bookings_router

app = FastAPI(title="Call Calendar API")
app.include_router(bookings_router)


@app.get("/health")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
