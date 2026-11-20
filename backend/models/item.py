from typing import TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import (
    Integer,
    String,
    Text,
    Boolean,
    CheckConstraint
)
from sqlalchemy.orm import Mapped, mapped_column

if TYPE_CHECKING:
    from .inventory import Inventory
    from .transaction import Transaction

from .base import Base


class Item(Base):
    __tablename__ = "items"

    __table_args__ = (
        CheckConstraint("price >= 0", name="check_item_price"),
        CheckConstraint(
            "effect_value >= 0",
            name="check_item_effect_value"
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    item_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False
    )

    price: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    effect_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False
    )

    effect_value: Mapped[int] = mapped_column(
        Integer,
    nullable=False
    )

    is_available: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )
    inventories: Mapped[list["Inventory"]] = relationship(
        "Inventory",
        back_populates="item",
        cascade="all, delete-orphan"
    )

    transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction",
        back_populates="item"
    )


