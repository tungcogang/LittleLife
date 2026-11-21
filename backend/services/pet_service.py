"""Các hàm hỗ trợ trạng thái pet, dùng chung cho route Pet, Care, Habit và Inventory."""

from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from backend.constants import (
    DAILY_HAPPINESS_DECAY,
    DAILY_HEALTH_DECAY,
    EXP_PER_LEVEL,
)
from backend.models.pet import Pet


def apply_daily_decay(db: Session, pet: Pet) -> bool:
    """Áp dụng mức giảm Happiness/Health mỗi ngày một lần cho ``pet``.

    Phải được gọi trước mọi thay đổi trạng thái pet khác trong cùng một
    transaction. Bên gọi chịu trách nhiệm commit, nhờ vậy hành động chăm sóc,
    phần thưởng habit hay việc dùng item và mức giảm được ghi nhận cùng lúc.

    Trả về ``True`` khi có áp dụng mức giảm. ``last_decay_date`` bằng NULL chỉ
    xác lập mốc của hôm nay (dùng khi pet được tạo ngoài API hoặc được migrate
    từ database cũ), nên pet không bao giờ bị trừ hai lần cho một khoảng thời
    gian không xác định.

    Dòng dữ liệu được khóa bằng ``SELECT ... FOR UPDATE`` và ngày của nó được
    đọc lại sau khi đã có khóa, nhờ đó hai request đồng thời không thể cùng áp
    dụng mức giảm của một ngày.
    """
    today = date.today()

    if pet.last_decay_date is not None and pet.last_decay_date >= today:
        return False

    locked = (
        db.query(Pet)
        .filter(Pet.id == pet.id)
        .with_for_update()
        .populate_existing()
        .one()
    )

    if locked.last_decay_date is not None and locked.last_decay_date >= today:
        return False

    if locked.last_decay_date is None:
        locked.last_decay_date = today
        db.flush()
        return False

    locked.happiness = max(0, locked.happiness - DAILY_HAPPINESS_DECAY)
    locked.health = max(0, locked.health - DAILY_HEALTH_DECAY)
    locked.last_decay_date = today
    db.flush()
    return True


def pet_snapshot(pet: Pet) -> dict[str, Any]:
    """Toàn bộ trạng thái pet chuẩn tắc mà các endpoint gameplay trả về."""
    return {
        "id": pet.id,
        "pet_name": pet.pet_name,
        "level": pet.level,
        "exp": pet.exp,
        "exp_to_next_level": EXP_PER_LEVEL,
        "hunger": pet.hunger,
        "happiness": pet.happiness,
        "energy": pet.energy,
        "health": pet.health,
        "last_decay_date": (
            pet.last_decay_date.isoformat() if pet.last_decay_date else None
        ),
    }
