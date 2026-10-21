from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.exercise import Exercise
    from app.models.session_error import SessionError
    from app.models.user import User


class WorkoutSession(Base):
    __tablename__ = "workout_sessions"

    session_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        index=True,
    )
    exercise_id: Mapped[int] = mapped_column(
        ForeignKey("exercises.exercise_id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        index=True,
    )
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    duration_sec: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Workout duration in seconds.",
    )
    total_reps: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Number of repetitions.",
    )

    user: Mapped["User"] = relationship(back_populates="workout_sessions")
    exercise: Mapped["Exercise"] = relationship(back_populates="workout_sessions")
    session_errors: Mapped[list["SessionError"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
    )
