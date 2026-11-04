from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.exercise import ExerciseRead
from app.services.exercises import get_exercise, list_exercises

router = APIRouter()


# Список упражнений.
@router.get("", response_model=list[ExerciseRead])
async def read_exercises(db: AsyncSession = Depends(get_db)) -> list[ExerciseRead]:
    exercises = await list_exercises(db)
    return [ExerciseRead.model_validate(exercise) for exercise in exercises]


# Карточка одного упражнения.
@router.get("/{exercise_id}", response_model=ExerciseRead)
async def read_exercise(
    exercise_id: int,
    db: AsyncSession = Depends(get_db),
) -> ExerciseRead:
    exercise = await get_exercise(db, exercise_id)
    return ExerciseRead.model_validate(exercise)
