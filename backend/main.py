from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.database import SessionLocal, engine
from backend.migrations import ensure_schema
from backend.routes.auth import router as auth_router
from backend.routes.pet import router as pet_router
from backend.routes.habit import router as habit_router
from backend.routes.care import router as care_router
from backend.routes.store import router as store_router
from backend.routes.inventory import router as inventory_router
from backend.services.item_service import ensure_catalog


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Nâng cấp các bảng hiện có và đồng bộ catalog của Store trước khi phục vụ
    # request. Cả hai thao tác đều idempotent và không làm mất dữ liệu.
    ensure_schema(engine)

    db = SessionLocal()
    try:
        ensure_catalog(db)
    finally:
        db.close()

    yield


app = FastAPI(
    title="LittleLife API",
    description="Backend for LittleLife Virtual Pet Game",
    version="1.1.0",
    lifespan=lifespan,
)

app.include_router(auth_router)
app.include_router(pet_router)
app.include_router(habit_router)
app.include_router(care_router)
app.include_router(store_router)
app.include_router(inventory_router)


@app.get("/")
def home():
    return {
        "message": "Welcome to LittleLife API!",
        "status": "running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }
