from fastapi import FastAPI

from backend.routes.auth import router as auth_router
from backend.routes.pet import router as pet_router
from backend.routes.habit import router as habit_router
from backend.routes.care import router as care_router

app = FastAPI(
    title="LittleLife API",
    description="Backend for LittleLife Virtual Pet Game",
    version="1.0.0"
)

app.include_router(auth_router)
app.include_router(pet_router)
app.include_router(habit_router)
app.include_router(care_router)


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
