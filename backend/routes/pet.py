from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.pet import Pet
from backend.models.user import User
from backend.services.auth_dependency import get_current_user
from backend.services.pet_service import apply_daily_decay, pet_snapshot

router = APIRouter(prefix="/pets", tags=["Pet"])


class CreatePetRequest(BaseModel):
    pet_name: str = Field(min_length=1, max_length=50)


@router.post("/create")
def create_pet(
    request: CreatePetRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Kiểm tra user đã có Pet chưa
    existing_pet = db.query(Pet).filter(
        Pet.user_id == current_user.id
    ).first()

    if existing_pet:
        raise HTTPException(
            status_code=409,
            detail="You already have a pet"
        )

    pet_name = request.pet_name.strip()

    if not pet_name:
        raise HTTPException(
            status_code=400,
            detail="Pet name cannot be empty"
        )

    # Pet mới bắt đầu với chỉ số "vừa nhận nuôi" giống Offline Demo
    # Mode (75/80/60/95) để mọi item trong Store đều có tác dụng rõ ràng.
    pet = Pet(
        user_id=current_user.id,
        pet_name=pet_name,
        level=1,
        exp=0,
        hunger=75,
        happiness=80,
        energy=60,
        health=95,
        last_decay_date=date.today()
    )

    db.add(pet)
    db.commit()
    db.refresh(pet)

    response = pet_snapshot(pet)
    response["message"] = "Pet created successfully"
    return response


@router.get("/me")
def get_my_pet(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    pet = db.query(Pet).filter(
        Pet.user_id == current_user.id
    ).first()

    if pet is None:
        raise HTTPException(
            status_code=404,
            detail="Pet not found"
        )

    # Request pet đầu tiên của một ngày mới sẽ áp dụng mức giảm Happiness/Health một lần.
    apply_daily_decay(db, pet)
    db.commit()
    db.refresh(pet)

    return pet_snapshot(pet)
