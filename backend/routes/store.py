"""Các endpoint Store: xem catalog và mua item bằng Coin."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.inventory import Inventory
from backend.models.item import Item
from backend.models.transaction import Transaction
from backend.models.user import User
from backend.services.auth_dependency import get_current_user
from backend.services.item_service import (
    ensure_catalog,
    list_inventory,
    serialize_item,
)

router = APIRouter(prefix="/store", tags=["Store"])


@router.get("/items")
def get_store_items(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trả về catalog đang bán cùng số Coin hiện tại của người chơi."""
    ensure_catalog(db)

    # Chỉ lấy các item đang bán (bỏ qua cảnh báo E712 của SQLAlchemy)
    items = (
        db.query(Item)
        .filter(Item.is_available == True)  # noqa: E712
        .order_by(Item.id.asc())
        .all()
    )

    return {
        "coins": current_user.coins,
        "items": [serialize_item(item) for item in items],
    }


@router.post("/buy/{item_id}")
def buy_store_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mua một đơn vị của một item.

    Việc trừ Coin, cập nhật inventory và ghi log transaction đều diễn ra trong
    cùng một database transaction, nên một lượt mua không bao giờ thành công nửa vời.
    """
    ensure_catalog(db)

    item = db.query(Item).filter(Item.id == item_id).first()

    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    if not item.is_available:
        raise HTTPException(status_code=409, detail=f"{item.name} is not available")

    try:
        # Tuần tự hóa các lượt mua đồng thời của người chơi này, rồi kiểm tra lại Coin.
        # Auth đã load user trước đó, nên populate_existing buộc đọc lại số dư
        # sau khi đã giữ khóa; nếu không, request thứ hai có thể dùng Coin cũ.
        user = (
            db.query(User)
            .filter(User.id == current_user.id)
            .with_for_update()
            .populate_existing()
            .one()
        )

        if user.coins < item.price:
            db.rollback()
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Not enough Coins. {item.name} costs {item.price} "
                    f"but you only have {user.coins}."
                ),
            )

        user.coins -= item.price

        inventory_row = (
            db.query(Inventory)
            .filter(
                Inventory.user_id == user.id,
                Inventory.item_id == item.id,
            )
            .with_for_update()
            .first()
        )

        if inventory_row is None:
            inventory_row = Inventory(
                user_id=user.id,
                item_id=item.id,
                quantity=1,
            )
            db.add(inventory_row)
        else:
            inventory_row.quantity += 1

        db.add(
            Transaction(
                user_id=user.id,
                item_id=item.id,
                transaction_type="purchase",
                amount=item.price,
                description=f"Purchased {item.name}",
            )
        )

        db.commit()

    except HTTPException:
        raise
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Purchase failed and no Coins were deducted. Please try again.",
        )

    quantity = inventory_row.quantity

    return {
        "message": f"Purchased {item.name}!",
        "item": serialize_item(item),
        "quantity": quantity,
        "coins": user.coins,
        "inventory": list_inventory(db, user.id),
    }
