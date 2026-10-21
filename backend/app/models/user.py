from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.workout_session import WorkoutSession


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    reset_token: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Password reset token sent to the user by email.",
    )
    reset_token_expiry: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    workout_sessions: Mapped[list["WorkoutSession"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
