from typing import TYPE_CHECKING
from sqlalchemy import (
    Integer,
    String,
    ForeignKey,
    CheckConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .user import User


class Pet(Base):
    __tablename__ = "pets"

    __table_args__ = (
        CheckConstraint("level >= 1", name="check_pet_level"),
        CheckConstraint("exp >= 0", name="check_pet_exp"),
        CheckConstraint(
            "hunger BETWEEN 0 AND 100",
            name="check_pet_hunger"
        ),
        CheckConstraint(
            "happiness BETWEEN 0 AND 100",
            name="check_pet_happiness"
        ),
        CheckConstraint(
            "energy BETWEEN 0 AND 100",
            name="check_pet_energy"
        ),
        CheckConstraint(
            "health BETWEEN 0 AND 100",
            name="check_pet_health"
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )

    pet_name: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    level: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False
    )

    exp: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    hunger: Mapped[int] = mapped_column(
        Integer,
        default=100,
        nullable=False
    )

    happiness: Mapped[int] = mapped_column(
        Integer,
        default=100,
        nullable=False
    )

    energy: Mapped[int] = mapped_column(
        Integer,
        default=100,
        nullable=False
    )

    health: Mapped[int] = mapped_column(
        Integer,
        default=100,
        nullable=False
    )

    # Quan hệ với User
    user: Mapped["User"] = relationship(
        back_populates="pet"
    )
