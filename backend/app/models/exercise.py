from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.workout_session import WorkoutSession


class TargetMuscleGroup(str, PyEnum):
    CHEST = "chest"
    BACK = "back"
    LEGS = "legs"
    SHOULDERS = "shoulders"
    ARMS = "arms"
    CORE = "core"
    FULL_BODY = "full_body"


class Exercise(Base):
    __tablename__ = "exercises"

    exercise_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(45), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    target_muscle_group: Mapped[TargetMuscleGroup | None] = mapped_column(
        Enum(
            TargetMuscleGroup,
            name="target_muscle_group",
            native_enum=True,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=True,
    )

    workout_sessions: Mapped[list["WorkoutSession"]] = relationship(
        back_populates="exercise",
        cascade="all, delete-orphan",
    )
