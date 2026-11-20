
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Integer,
    Date,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .habit import Habit


class HabitCompletion(Base):
    __tablename__ = "habit_completions"

    __table_args__ = (
        UniqueConstraint(
            "habit_id",
            "completed_date",
            name="unique_habit_completion_per_day"
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    habit_id: Mapped[int] = mapped_column(
        ForeignKey("habits.id", ondelete="CASCADE"),
        nullable=False
    )

    completed_date: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    completed_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )

    coins_earned: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    exp_earned: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    habit: Mapped["Habit"] = relationship(
        "Habit",
        back_populates="completions"
    )
