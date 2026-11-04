from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.exercise import Exercise


# Возвращает каталог упражнений.
async def list_exercises(db: AsyncSession) -> list[Exercise]:
    exercises = await db.scalars(select(Exercise).order_by(Exercise.name))
    return list(exercises.all())


# Возвращает одно упражнение или 404.
async def get_exercise(db: AsyncSession, exercise_id: int) -> Exercise:
    exercise = await db.get(Exercise, exercise_id)
    if exercise is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercise not found",
        )
    return exercise
