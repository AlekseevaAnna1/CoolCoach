from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.workout_session import WorkoutSession


class SessionError(Base):
    __tablename__ = "session_errors"

    error_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("workout_sessions.session_id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        index=True,
    )
    error_type: Mapped[str] = mapped_column(String(45), nullable=False)
    error_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="How many times this error type occurred during the workout.",
    )
    first_occurred_sec: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Second of the workout when this error first appeared.",
    )

    session: Mapped["WorkoutSession"] = relationship(back_populates="session_errors")
