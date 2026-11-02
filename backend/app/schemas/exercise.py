from pydantic import BaseModel, ConfigDict, Field

from app.models.exercise import TargetMuscleGroup


class ExerciseCreate(BaseModel): // описывает JSON, который клиент отправляет серверу при создании упражнения
    name: str = Field(max_length=45)
    description: str | None = Field(default=None, max_length=255)
    target_muscle_group: TargetMuscleGroup | None = None


class ExerciseRead(BaseModel): // описывает JSON, который сервер отдаёт клиенту после получения упражнения
    model_config = ConfigDict(from_attributes=True)

    exercise_id: int
    name: str
    description: str | None
    target_muscle_group: TargetMuscleGroup | None
