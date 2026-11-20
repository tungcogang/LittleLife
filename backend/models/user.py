from typing import TYPE_CHECKING


from datetime import datetime

from sqlalchemy import (
    String,
    Integer,
    DateTime,
    CheckConstraint,
    func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .pet import Pet
    from .habit import Habit
    from .inventory import Inventory
    from .transaction import Transaction


class User(Base):
    __tablename__ = "users"

    __table_args__ = (
        CheckConstraint("coins >= 0", name="check_user_coins"),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    coins: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    role: Mapped[str] = mapped_column(
        String(20),
        default="user",
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )

    # Quan hệ với Pet
    pet: Mapped["Pet | None"] = relationship(
        "Pet",
        back_populates="user",
        uselist=False
    )

    habits: Mapped[list["Habit"]] = relationship(
        "Habit",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    inventory: Mapped[list["Inventory"]] = relationship(
        "Inventory",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction",
        back_populates="user",
        cascade="all, delete-orphan"
    )
