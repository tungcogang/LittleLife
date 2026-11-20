
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.pet import Pet
from backend.models.user import User
from backend.services.auth_dependency import get_current_user

router = APIRouter(prefix="/care", tags=["Pet Care"])


def get_user_pet(db: Session, user_id: int):
    pet = db.query(Pet).filter(Pet.user_id == user_id).first()

    if not pet:
        raise HTTPException(
            status_code=404,
            detail="Pet not found"
        )

    return pet


@router.post("/feed")
def feed_pet(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    pet = get_user_pet(db, current_user.id)

    pet.hunger = min(100, pet.hunger + 30)

    db.commit()
    db.refresh(pet)

    return {
        "message": "Pet fed successfully",
        "pet_name": pet.pet_name,
        "hunger": pet.hunger
    }


@router.post("/play")
def play_with_pet(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    pet = get_user_pet(db, current_user.id)

    if pet.energy < 20:
        raise HTTPException(
            status_code=400,
            detail="Not enough energy to play"
        )

    pet.happiness = min(100, pet.happiness + 20)
    pet.energy = max(0, pet.energy - 20)

    db.commit()
    db.refresh(pet)

    return {
        "message": "Played with pet successfully",
        "pet_name": pet.pet_name,
        "happiness": pet.happiness,
        "energy": pet.energy
    }


@router.post("/rest")
def rest_pet(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    pet = get_user_pet(db, current_user.id)

    pet.energy = min(100, pet.energy + 30)

    db.commit()
    db.refresh(pet)

    return {
        "message": "Pet rested successfully",
        "pet_name": pet.pet_name,
        "energy": pet.energy
    }
