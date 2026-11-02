from pydantic import BaseModel, ConfigDict, Field

from app.models.exercise import TargetMuscleGroup


# Описывает JSON, который клиент отправляет серверу при создании упражнения.
class ExerciseCreate(BaseModel):
    name: str = Field(max_length=45)
    description: str | None = Field(default=None, max_length=255)
    target_muscle_group: TargetMuscleGroup | None = None


# Описывает JSON, который сервер отдаёт клиенту после получения упражнения.
class ExerciseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    exercise_id: int
    name: str
    description: str | None
    target_muscle_group: TargetMuscleGroup | None
