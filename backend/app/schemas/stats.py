from datetime import date

from pydantic import BaseModel, Field


# Ответ экрана истории: календарь тренировок и краткая справка о прогрессе.
class StatsRead(BaseModel):
    calendar: dict[date, int] = Field(
        description="Дата начала тренировки и число тренировок в этот день. Дни без тренировок не включаются. Детали выбранного дня отдаются списком WorkoutHistoryItem.",
        examples=[{"2023-10-01": 1, "2023-10-03": 2}],
    )
    streak_days: int = Field(
        ge=0,
        description="Сколько дней подряд, включая сегодня, пользователь тренировался.",
    )
    error_rate_percent: float | None = Field(
        default=None,
        description="Процент ошибок на повторение за последние 30 дней: сумма error_count / сумма total_reps * 100. null, если повторений не было.",
    )
    previous_error_rate_percent: float | None = Field(  
        default=None,
        description="Тот же процент за предыдущие 30 дней. null, если в том окне не было повторений.",
    )
    top_error_type: str | None = Field(
        default=None,
        description="error_type с наибольшей суммой error_count за последние 30 дней.",
    )
    top_error_share_percent: float | None = Field(
        default=None,
        description="Доля топ-1 типа среди всех ошибок за последние 30 дней. null, если ошибок не было.",
    )
