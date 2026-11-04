from datetime import date, datetime, time, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.exercise import Exercise
from app.models.session_error import SessionError
from app.models.user import User
from app.models.workout_session import WorkoutSession
from app.schemas.workout_session import WorkoutHistoryItem, WorkoutSessionCreate

# Преобразует datetime в naive datetime
def _as_naive_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)


# Сохраняет законченную тренировку и её ошибки.
async def create_workout(
    db: AsyncSession,
    user: User,
    data: WorkoutSessionCreate,
) -> WorkoutSession:
    exercise = await db.get(Exercise, data.exercise_id)
    if exercise is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercise not found",
        )

    workout = WorkoutSession(
        user_id=user.user_id,
        exercise_id=data.exercise_id,
        started_at=_as_naive_utc(data.started_at),
        duration_sec=data.duration_sec,
        total_reps=data.total_reps,
    )
    db.add(workout)
    await db.flush()

    last_error_id = await db.scalar(select(func.max(SessionError.error_id)))
    next_error_id = 0 if last_error_id is None else last_error_id
    for error in data.errors:
        next_error_id += 1
        db.add(
            SessionError(
                error_id=next_error_id,
                session_id=workout.session_id,
                error_type=error.error_type,
                error_count=error.error_count,
                first_occurred_sec=error.first_occurred_sec,
            )
        )

    await db.commit()
    stored = await db.scalar(
        select(WorkoutSession)
        .where(WorkoutSession.session_id == workout.session_id)
        .options(selectinload(WorkoutSession.session_errors))
    )
    if stored is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Workout was not saved",
        )
    return stored


# Тренировки пользователя за выбранный день.
async def list_workouts_on_date(
    db: AsyncSession,
    user: User,
    workout_date: date,
) -> list[WorkoutHistoryItem]:
    day_start = datetime.combine(workout_date, time.min)
    day_end = day_start + timedelta(days=1)
    workouts = await db.scalars(
        select(WorkoutSession)
        .where(
            WorkoutSession.user_id == user.user_id,
            WorkoutSession.started_at >= day_start,
            WorkoutSession.started_at < day_end,
        )
        .options(
            selectinload(WorkoutSession.exercise),
            selectinload(WorkoutSession.session_errors),
        )
        .order_by(WorkoutSession.started_at)
    )
    return [
        WorkoutHistoryItem(
            session_id=workout.session_id,
            exercise_name=workout.exercise.name,
            started_at=workout.started_at,
            duration_sec=workout.duration_sec,
            total_reps=workout.total_reps,
            error_count=sum(error.error_count for error in workout.session_errors),
        )
        for workout in workouts.all()
    ]


# Удаляет тренировку текущего пользователя.
async def delete_workout(db: AsyncSession, user: User, session_id: int) -> None:
    workout = await db.get(WorkoutSession, session_id)
    if workout is None or workout.user_id != user.user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workout not found",
        )
    await db.delete(workout)
    await db.commit()
