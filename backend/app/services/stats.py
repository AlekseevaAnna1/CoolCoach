from collections import Counter
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.models.workout_session import WorkoutSession
from app.schemas.stats import StatsRead

PROGRESS_WINDOW_DAYS = 30

# Сколько дней подряд тренировался пользователь на сегодняшний день
def _streak_days(workout_dates: set[date], today: date) -> int:
    cursor = today if today in workout_dates else today - timedelta(days=1)
    streak = 0
    while cursor in workout_dates:
        streak += 1
        cursor -= timedelta(days=1)
    return streak

# Процент ошибок в тренировке
def _error_rate(workouts: list[WorkoutSession]) -> float | None:
    total_reps = sum(workout.total_reps for workout in workouts)
    if total_reps == 0:
        return None
    total_errors = sum(error.error_count for workout in workouts for error in workout.session_errors)
    return round(total_errors / total_reps * 100, 1)


def _top_error(workouts: list[WorkoutSession]) -> tuple[str | None, float | None]:
    counts: Counter[str] = Counter()
    for workout in workouts:
        for error in workout.session_errors:
            counts[error.error_type] += error.error_count
    if not counts:
        return None, None
    error_type, error_count = counts.most_common(1)[0]
    share = round(error_count / sum(counts.values()) * 100, 1)
    return error_type, share


# Календарь, серия и метрики прогресса текущего пользователя.
async def get_user_stats(db: AsyncSession, user: User) -> StatsRead:
    workouts = list(
        (
            await db.scalars(
                select(WorkoutSession)
                .where(WorkoutSession.user_id == user.user_id)
                .options(selectinload(WorkoutSession.session_errors))
            )
        ).all()
    )
    calendar = dict(
        sorted(Counter(workout.started_at.date() for workout in workouts).items())
    )
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    current_start = now - timedelta(days=PROGRESS_WINDOW_DAYS)
    previous_start = now - timedelta(days=PROGRESS_WINDOW_DAYS * 2)
    current_workouts = [workout for workout in workouts if workout.started_at >= current_start]
    previous_workouts = [
        workout
        for workout in workouts
        if previous_start <= workout.started_at < current_start
    ]
    top_error_type, top_error_share_percent = _top_error(current_workouts)
    return StatsRead(
        calendar=calendar,
        streak_days=_streak_days(set(calendar), now.date()),
        error_rate_percent=_error_rate(current_workouts),
        previous_error_rate_percent=_error_rate(previous_workouts),
        top_error_type=top_error_type,
        top_error_share_percent=top_error_share_percent,
    )
