from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.session_error import SessionErrorCreate, SessionErrorRead


class WorkoutSessionCreate(BaseModel):
    exercise_id: int
    started_at: datetime
    duration_sec: int = Field(ge=0)
    total_reps: int = Field(ge=0)
    errors: list[SessionErrorCreate] = Field(default_factory=list)


class WorkoutSessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    session_id: int
    user_id: int
    exercise_id: int
    started_at: datetime
    duration_sec: int
    total_reps: int
    session_errors: list[SessionErrorRead] = Field(default_factory=list)
