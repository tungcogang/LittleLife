"""Các endpoint Inventory: liệt kê item đang sở hữu và dùng chúng cho pet."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.inventory import Inventory
from backend.models.item import Item
from backend.models.pet import Pet
from backend.models.user import User
from backend.services.auth_dependency import get_current_user
from backend.services.item_service import (
    apply_item_effects,
    list_inventory,
    serialize_item,
)
from backend.services.pet_service import apply_daily_decay, pet_snapshot

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.get("/")
def get_inventory(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trả về toàn bộ item đang sở hữu cùng số Coin hiện tại."""
    return {
        "coins": current_user.coins,
        "items": list_inventory(db, current_user.id),
    }


@router.post("/{item_id}/use")
def use_inventory_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Tiêu hao một item và áp dụng hiệu ứng của nó lên pet của người chơi.

    Dòng inventory, chỉ số pet và việc xóa stack rỗng đều được commit cùng nhau.
    Item chỉ bị trừ sau khi đã áp dụng được ít nhất một hiệu ứng, và việc dùng
    item bị từ chối khi mọi chỉ số mục tiêu đều đã đầy.
    """
    try:
        inventory_row = (
            db.query(Inventory)
            .filter(
                Inventory.user_id == current_user.id,
                Inventory.item_id == item_id,
            )
            .with_for_update()
            .first()
        )

        if inventory_row is None or inventory_row.quantity <= 0:
            raise HTTPException(
                status_code=404,
                detail="You do not own this item.",
            )

        item = db.query(Item).filter(Item.id == item_id).first()

        if item is None:
            raise HTTPException(status_code=404, detail="Item not found")

        pet = (
            db.query(Pet)
            .filter(Pet.user_id == current_user.id)
            .with_for_update()
            .first()
        )

        if pet is None:
            raise HTTPException(status_code=404, detail="Pet not found")

        # Lần tương tác pet đầu tiên của ngày mới: áp dụng mức giảm hằng ngày cùng
        # với hiệu ứng của item trong cùng một transaction.
        apply_daily_decay(db, pet)

        try:
            applied_effects = apply_item_effects(pet, item)
        except ValueError as error:
            db.rollback()
            raise HTTPException(status_code=400, detail=str(error))

        remaining_quantity = inventory_row.quantity - 1

        if remaining_quantity <= 0:
            db.delete(inventory_row)
        else:
            inventory_row.quantity = remaining_quantity

        db.commit()

    except HTTPException:
        raise
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Item could not be used and nothing was consumed. Please try again.",
        )

    return {
        "message": f"Used {item.name}!",
        "item": serialize_item(item),
        "quantity": max(0, remaining_quantity),
        "applied_effects": applied_effects,
        "pet": pet_snapshot(pet),
        "coins": current_user.coins,
        "inventory": list_inventory(db, current_user.id),
    }
