
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.pet import Pet
from backend.models.user import User
from backend.services.auth_dependency import get_current_user

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

    # Tạo Pet mới
    pet = Pet(
        user_id=current_user.id,
        pet_name=pet_name,
        level=1,
        exp=0,
        hunger=100,
        happiness=100,
        energy=100,
        health=100
    )

    db.add(pet)
    db.commit()
    db.refresh(pet)

    return {
        "message": "Pet created successfully",
        "id": pet.id,
        "pet_name": pet.pet_name,
        "level": pet.level,
        "exp": pet.exp,
        "hunger": pet.hunger,
        "happiness": pet.happiness,
        "energy": pet.energy,
        "health": pet.health
    }


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

    return {
        "id": pet.id,
        "pet_name": pet.pet_name,
        "level": pet.level,
        "exp": pet.exp,
        "hunger": pet.hunger,
        "happiness": pet.happiness,
        "energy": pet.energy,
        "health": pet.health
    }
