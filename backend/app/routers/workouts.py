from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.workout_session import WorkoutHistoryItem, WorkoutSessionCreate, WorkoutSessionRead
from app.services.auth import get_current_user
from app.services.workouts import create_workout, delete_workout, list_workouts_on_date

router = APIRouter()


# Сохранение законченной тренировки.
@router.post("", response_model=WorkoutSessionRead, status_code=status.HTTP_201_CREATED)
async def create_workout_session(
    payload: WorkoutSessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WorkoutSessionRead:
    workout = await create_workout(db, current_user, payload)
    return WorkoutSessionRead.model_validate(workout)


# Тренировки выбранного дня календаря.
@router.get("", response_model=list[WorkoutHistoryItem])
async def read_workouts_on_date(
    workout_date: Annotated[date, Query(alias="date")],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[WorkoutHistoryItem]:
    return await list_workouts_on_date(db, current_user, workout_date)


# Удаление своей тренировки.
@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_workout(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    await delete_workout(db, current_user, session_id)
