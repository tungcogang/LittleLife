
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend.database import get_db
from backend.models.habit import Habit
from backend.models.habit_completion import HabitCompletion
from backend.models.user import User
from backend.models.pet import Pet
from backend.services.auth_dependency import get_current_user

router = APIRouter(prefix="/habits", tags=["Habit"])

COINS_REWARD = 10
EXP_REWARD = 20
EXP_PER_LEVEL = 100


class CreateHabitRequest(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    description: str | None = None


@router.post("/create")
def create_habit(
    request: CreateHabitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    title = request.title.strip()

    if not title:
        raise HTTPException(
            status_code=400,
            detail="Habit title cannot be empty"
        )

    habit = Habit(
        user_id=current_user.id,
        title=title,
        description=request.description,
        is_active=True
    )

    db.add(habit)
    db.commit()
    db.refresh(habit)

    return {
        "message": "Habit created successfully",
        "id": habit.id,
        "title": habit.title,
        "description": habit.description,
        "is_active": habit.is_active
    }


@router.get("/")
def get_habits(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    habits = db.query(Habit).filter(
        Habit.user_id == current_user.id,
        Habit.is_active == True
    ).all()

    today = date.today()

    result = []

    for habit in habits:
        completed = db.query(HabitCompletion).filter(
            HabitCompletion.habit_id == habit.id,
            HabitCompletion.completed_date == today
        ).first() is not None

        result.append({
            "id": habit.id,
            "title": habit.title,
            "description": habit.description,
            "is_active": habit.is_active,
            "completed_today": completed
        })

    return result


@router.post("/{habit_id}/complete")
def complete_habit(
    habit_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    habit = db.query(Habit).filter(
        Habit.id == habit_id,
        Habit.user_id == current_user.id,
        Habit.is_active == True
    ).first()

    if not habit:
        raise HTTPException(
            status_code=404,
            detail="Habit not found"
        )

    today = date.today()

    existing_completion = db.query(HabitCompletion).filter(
        HabitCompletion.habit_id == habit.id,
        HabitCompletion.completed_date == today
    ).first()

    if existing_completion:
        raise HTTPException(
            status_code=409,
            detail="Habit already completed today"
        )

    pet = db.query(Pet).filter(
        Pet.user_id == current_user.id
    ).first()

    if not pet:
        raise HTTPException(
            status_code=404,
            detail="Pet not found"
        )

    completion = HabitCompletion(
        habit_id=habit.id,
        completed_date=today,
        coins_earned=COINS_REWARD,
        exp_earned=EXP_REWARD
    )

    current_user.coins += COINS_REWARD
    pet.exp += EXP_REWARD

    leveled_up = False

    while pet.exp >= EXP_PER_LEVEL:
        pet.exp -= EXP_PER_LEVEL
        pet.level += 1
        leveled_up = True

    db.add(completion)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Habit already completed today"
        )

    return {
        "message": "Habit completed successfully",
        "habit_id": habit.id,
        "habit_title": habit.title,
        "coins_earned": COINS_REWARD,
        "total_coins": current_user.coins,
        "exp_earned": EXP_REWARD,
        "pet_exp": pet.exp,
        "pet_level": pet.level,
        "leveled_up": leveled_up
    }
