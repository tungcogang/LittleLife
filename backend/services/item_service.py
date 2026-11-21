"""Catalog của Store, serialize inventory và các hàm hỗ trợ hiệu ứng cho pet.

Catalog được cố ý giữ nhỏ và bám theo các loại item mà UI Pygame đã biết cách
vẽ: food, toy, medicine, potion và comfort.
"""

from threading import Lock
from typing import Any

from sqlalchemy.orm import Session

from backend.constants import PET_STAT_LABELS, PET_STAT_MAX
from backend.models.inventory import Inventory
from backend.models.item import Item
from backend.models.pet import Pet


# Catalog item chuẩn của LittleLife. Giá/hiệu ứng khớp với catalog của frontend
# để Online và Offline/Demo Mode dạy người chơi cùng một bộ số. Id và giá của
# item hiện có được giữ nguyên; chỉ các giá trị hiệu ứng được cân bằng lại.
ITEM_CATALOG: list[dict[str, Any]] = [
    {
        "id": 101,
        "name": "Crispy Biscuit",
        "item_type": "food",
        "price": 15,
        "effect_type": "hunger",
        "effect_value": 30,
        "secondary_effect_type": None,
        "secondary_effect_value": None,
        "description": "A delicious home-baked cookie your pet loves.",
    },
    {
        "id": 102,
        "name": "Gourmet Salmon",
        "item_type": "food",
        "price": 40,
        "effect_type": "hunger",
        "effect_value": 55,
        "secondary_effect_type": None,
        "secondary_effect_value": None,
        "description": "Nutritious fresh salmon filet that fills the tummy.",
    },
    {
        "id": 103,
        "name": "Squeaky Ball",
        "item_type": "toy",
        "price": 25,
        "effect_type": "happiness",
        "effect_value": 30,
        "secondary_effect_type": None,
        "secondary_effect_value": None,
        "description": "Bright squeaky toy that brings endless joy.",
    },
    {
        "id": 104,
        "name": "Herbal Tonic",
        "item_type": "medicine",
        "price": 35,
        "effect_type": "health",
        "effect_value": 30,
        "secondary_effect_type": None,
        "secondary_effect_value": None,
        "description": "Soothing natural remedy to restore pet vitality.",
    },
    {
        "id": 105,
        "name": "Energy Elixir",
        "item_type": "potion",
        "price": 50,
        "effect_type": "energy",
        "effect_value": 30,
        "secondary_effect_type": None,
        "secondary_effect_value": None,
        "description": "Sparkling drink that instantly boosts pet stamina.",
    },
    {
        "id": 106,
        "name": "Cozy Pillow",
        "item_type": "comfort",
        "price": 40,
        "effect_type": "energy",
        "effect_value": 20,
        "secondary_effect_type": "health",
        "secondary_effect_value": 10,
        "description": "A soft, warm pillow that restores Energy and Health.",
    },
]

_CATALOG_LOCK = Lock()


def ensure_catalog(db: Session) -> None:
    """Tạo các item còn thiếu trong catalog và đồng bộ định nghĩa hiệu ứng của chúng.

    Thao tác này idempotent, không bao giờ đổi id hay giá của item đã có và
    không đụng tới dữ liệu người dùng, nên an toàn khi gọi ở mỗi lần khởi động
    (kể cả từ ``init_db``). Một lock toàn tiến trình ngăn các request đầu tiên
    chạy đồng thời cùng lúc khởi tạo những dòng giống nhau.
    """
    with _CATALOG_LOCK:
        existing_items = db.query(Item).all()
        existing_by_name = {item.name: item for item in existing_items}
        used_ids = {item.id for item in existing_items}
        next_id = (max(used_ids) if used_ids else 100) + 1

        changed = False

        for entry in ITEM_CATALOG:
            item = existing_by_name.get(entry["name"])

            if item is None:
                item_id = entry["id"]
                if item_id in used_ids:
                    # Không bao giờ ghi đè item đang dùng id chuẩn.
                    item_id = next_id
                    next_id += 1

                db.add(
                    Item(
                        id=item_id,
                        name=entry["name"],
                        item_type=entry["item_type"],
                        price=entry["price"],
                        effect_type=entry["effect_type"],
                        effect_value=entry["effect_value"],
                        secondary_effect_type=entry["secondary_effect_type"],
                        secondary_effect_value=entry["secondary_effect_value"],
                        description=entry["description"],
                        is_available=True,
                    )
                )
                used_ids.add(item_id)
                changed = True
                continue

            # Giữ nguyên id và giá hiện có; chỉ làm mới định nghĩa hiệu ứng.
            for field in (
                "effect_type",
                "effect_value",
                "secondary_effect_type",
                "secondary_effect_value",
            ):
                new_value = entry.get(field)
                if getattr(item, field) != new_value:
                    setattr(item, field, new_value)
                    changed = True

        if changed:
            db.commit()


def serialize_item(item: Item) -> dict[str, Any]:
    """Biểu diễn công khai của một item trong catalog."""
    return {
        "id": item.id,
        "name": item.name,
        "description": item.description or "",
        "item_type": item.item_type,
        "price": item.price,
        "effect_type": item.effect_type,
        "effect_value": item.effect_value,
        "secondary_effect_type": item.secondary_effect_type,
        "secondary_effect_value": item.secondary_effect_value,
    }


def serialize_inventory_entry(inventory: Inventory, item: Item) -> dict[str, Any]:
    """Biểu diễn công khai của một dòng inventory (item + số lượng sở hữu)."""
    entry = serialize_item(item)
    entry["item_id"] = item.id
    entry["quantity"] = inventory.quantity
    return entry


def list_inventory(db: Session, user_id: int) -> list[dict[str, Any]]:
    """Trả về mọi item đang sở hữu (quantity > 0) của một user, theo thứ tự catalog."""
    rows = (
        db.query(Inventory, Item)
        .join(Item, Inventory.item_id == Item.id)
        .filter(
            Inventory.user_id == user_id,
            Inventory.quantity > 0,
        )
        .order_by(Item.id.asc())
        .all()
    )
    return [serialize_inventory_entry(inv, item) for inv, item in rows]


def item_effect_pairs(item: Item) -> list[tuple[str, int]]:
    """Trả về hiệu ứng chính và hiệu ứng phụ tùy chọn của item."""
    pairs: list[tuple[str, int]] = []

    if item.effect_type and item.effect_value is not None:
        pairs.append((item.effect_type, item.effect_value))

    if item.secondary_effect_type and item.secondary_effect_value is not None:
        pairs.append((item.secondary_effect_type, item.secondary_effect_value))

    return pairs


def apply_item_effects(pet: Pet, item: Item) -> list[dict[str, Any]]:
    """Áp dụng mọi hiệu ứng còn tăng được của item và báo cáo những gì đã đổi.

    Ném ``ValueError`` khi item nhắm tới chỉ số không được hỗ trợ hoặc khi không
    hiệu ứng nào còn cải thiện được pet, để bên gọi từ chối việc dùng item
    *trước* khi tiêu hao nó. Item nhiều hiệu ứng vẫn được dùng khi còn ít nhất
    một chỉ số có thể cải thiện.
    """
    pairs = item_effect_pairs(item)

    if not pairs:
        raise ValueError(f"{item.name} has no usable effect.")

    for effect_type, _ in pairs:
        if effect_type not in PET_STAT_LABELS:
            raise ValueError(f"{item.name} has an unsupported effect.")

    applied: list[dict[str, Any]] = []
    full_labels: list[str] = []

    for effect_type, value in pairs:
        if value <= 0:
            continue

        current_value = getattr(pet, effect_type)

        if current_value >= PET_STAT_MAX:
            full_labels.append(PET_STAT_LABELS[effect_type])
            continue

        new_value = min(PET_STAT_MAX, current_value + value)
        setattr(pet, effect_type, new_value)
        applied.append({
            "type": effect_type,
            "value": new_value - current_value,
        })

    if not applied:
        if not full_labels:
            raise ValueError(f"{item.name} has no usable effect.")

        labels = " and ".join(full_labels)
        verb = "is" if len(full_labels) == 1 else "are"
        raise ValueError(f"{pet.pet_name}'s {labels} {verb} already full!")

    return applied
