
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.constants import (
    FEED_HUNGER_GAIN,
    PET_STAT_MAX,
    PLAY_ENERGY_COST,
    PLAY_HAPPINESS_GAIN,
    PLAY_HUNGER_COST,
    SLEEP_ENERGY_GAIN,
    SLEEP_HEALTH_GAIN,
)
from backend.database import get_db
from backend.models.pet import Pet
from backend.models.user import User
from backend.services.auth_dependency import get_current_user
from backend.services.pet_service import apply_daily_decay, pet_snapshot

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
    apply_daily_decay(db, pet)

    if pet.hunger >= PET_STAT_MAX:
        raise HTTPException(
            status_code=400,
            detail=f"{pet.pet_name} is already full!"
        )

    pet.hunger = min(PET_STAT_MAX, pet.hunger + FEED_HUNGER_GAIN)

    db.commit()
    db.refresh(pet)

    return {
        "message": "Pet fed successfully",
        "pet_name": pet.pet_name,
        "hunger": pet.hunger,
        "pet": pet_snapshot(pet)
    }


@router.post("/play")
def play_with_pet(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    pet = get_user_pet(db, current_user.id)
    apply_daily_decay(db, pet)

    if pet.hunger < PLAY_HUNGER_COST:
        raise HTTPException(
            status_code=400,
            detail=f"{pet.pet_name} is too hungry to play! Feed them first."
        )

    if pet.energy < PLAY_ENERGY_COST:
        raise HTTPException(
            status_code=400,
            detail=f"{pet.pet_name} is too tired to play! Let them rest."
        )

    pet.hunger = max(0, pet.hunger - PLAY_HUNGER_COST)
    pet.energy = max(0, pet.energy - PLAY_ENERGY_COST)
    pet.happiness = min(PET_STAT_MAX, pet.happiness + PLAY_HAPPINESS_GAIN)

    db.commit()
    db.refresh(pet)

    return {
        "message": "Played with pet successfully",
        "pet_name": pet.pet_name,
        "happiness": pet.happiness,
        "energy": pet.energy,
        "hunger": pet.hunger,
        "pet": pet_snapshot(pet)
    }


@router.post("/rest")
def rest_pet(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    pet = get_user_pet(db, current_user.id)
    apply_daily_decay(db, pet)

    if pet.energy >= PET_STAT_MAX and pet.health >= PET_STAT_MAX:
        raise HTTPException(
            status_code=400,
            detail=f"{pet.pet_name} is already fully rested and healthy!"
        )

    pet.energy = min(PET_STAT_MAX, pet.energy + SLEEP_ENERGY_GAIN)
    pet.health = min(PET_STAT_MAX, pet.health + SLEEP_HEALTH_GAIN)

    db.commit()
    db.refresh(pet)

    return {
        "message": "Pet rested successfully",
        "pet_name": pet.pet_name,
        "energy": pet.energy,
        "health": pet.health,
        "pet": pet_snapshot(pet)
    }
