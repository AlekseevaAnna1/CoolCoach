from fastapi import FastAPI

from app.routers import auth, stats, workouts

app = FastAPI(title="CoolCoach API", version="0.1.0")

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(workouts.router, prefix="/workouts", tags=["workouts"])
app.include_router(stats.router, prefix="/stats", tags=["stats"])


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
