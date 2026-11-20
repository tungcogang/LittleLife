"""
Mock data store and domain models for LittleLife UI prototype.
Maintains state locally and simulates game actions (feed, play, sleep, habit completion, buy, use).
"""
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional


@dataclass
class PetState:
    pet_name: str = "Mochi"
    level: int = 1
    exp: int = 45
    exp_to_next_level: int = 100
    hunger: int = 75       # 0 - 100
    happiness: int = 80    # 0 - 100
    energy: int = 60       # 0 - 100
    health: int = 95       # 0 - 100

    def gain_exp(self, amount: int):
        self.exp += amount
        while self.exp >= self.exp_to_next_level:
            self.exp -= self.exp_to_next_level
            self.level += 1
            self.exp_to_next_level = int(self.exp_to_next_level * 1.5)


@dataclass
class HabitItem:
    id: int
    title: str
    description: str
    category: str
    reward_coins: int
    reward_exp: int
    completed: bool = False


@dataclass
class ShopItem:
    id: int
    name: str
    item_type: str        # "food", "toy", "medicine", "potion"
    price: int
    effect_type: str      # "hunger", "happiness", "energy", "health"
    effect_value: int
    description: str


@dataclass
class InventoryItem:
    item_id: int
    item: ShopItem
    quantity: int


class MockDataStore:
    """Centralized mock data store representing backend state."""
    def __init__(self):
        self.user_coins: int = 150
        self.pet: PetState = PetState()

        self.habits: List[HabitItem] = [
            HabitItem(
                id=1,
                title="Morning Water",
                description="Drink 500ml of clean warm water after waking up",
                category="Health",
                reward_coins=15,
                reward_exp=20,
                completed=False
            ),
            HabitItem(
                id=2,
                title="30-min Reading",
                description="Read a programming book or inspiring novel",
                category="Learning",
                reward_coins=25,
                reward_exp=35,
                completed=True
            ),
            HabitItem(
                id=3,
                title="Afternoon Walk",
                description="Get some fresh air and walk for at least 15 minutes",
                category="Fitness",
                reward_coins=20,
                reward_exp=25,
                completed=False
            ),
            HabitItem(
                id=4,
                title="Sleep before 11 PM",
                description="Wind down screen time and get 8 hours of sleep",
                category="Rest",
                reward_coins=30,
                reward_exp=30,
                completed=False
            ),
        ]

        # Available shop items catalog
        self.shop_catalog: List[ShopItem] = [
            ShopItem(
                id=101,
                name="Crispy Biscuit",
                item_type="food",
                price=15,
                effect_type="hunger",
                effect_value=25,
                description="A delicious home-baked cookie your pet loves."
            ),
            ShopItem(
                id=102,
                name="Gourmet Salmon",
                item_type="food",
                price=40,
                effect_type="hunger",
                effect_value=55,
                description="Nutritious fresh salmon filet that fills the tummy."
            ),
            ShopItem(
                id=103,
                name="Squeaky Ball",
                item_type="toy",
                price=25,
                effect_type="happiness",
                effect_value=30,
                description="Bright squeaky toy that brings endless joy."
            ),
            ShopItem(
                id=104,
                name="Herbal Tonic",
                item_type="medicine",
                price=35,
                effect_type="health",
                effect_value=40,
                description="Soothing natural remedy to restore pet vitality."
            ),
            ShopItem(
                id=105,
                name="Energy Elixir",
                item_type="potion",
                price=50,
                effect_type="energy",
                effect_value=50,
                description="Sparkling drink that instantly boosts pet stamina."
            ),
        ]

        # User's starting inventory
        self.inventory: Dict[int, InventoryItem] = {
            101: InventoryItem(item_id=101, item=self.shop_catalog[0], quantity=3),
            103: InventoryItem(item_id=103, item=self.shop_catalog[2], quantity=1),
        }

    # --- Pet Actions ---
    def feed_pet(self) -> Tuple[bool, str]:
        if self.pet.hunger >= 100:
            return False, f"{self.pet.pet_name} is already full!"
        self.pet.hunger = min(100, self.pet.hunger + 20)
        self.pet.happiness = min(100, self.pet.happiness + 5)
        self.pet.gain_exp(10)
        return True, f"Fed {self.pet.pet_name}! (+20 Hunger, +10 EXP)"

    def play_with_pet(self) -> Tuple[bool, str]:
        if self.pet.energy < 15:
            return False, f"{self.pet.pet_name} is too tired to play! Let them rest."
        self.pet.energy = max(0, self.pet.energy - 15)
        self.pet.happiness = min(100, self.pet.happiness + 25)
        self.pet.hunger = max(0, self.pet.hunger - 10)
        self.pet.gain_exp(15)
        return True, f"Played with {self.pet.pet_name}! (+25 Happiness, -15 Energy, +15 EXP)"

    def pet_sleep(self) -> Tuple[bool, str]:
        if self.pet.energy >= 100:
            return False, f"{self.pet.pet_name} is fully energized and not sleepy!"
        self.pet.energy = min(100, self.pet.energy + 40)
        self.pet.health = min(100, self.pet.health + 10)
        self.pet.gain_exp(10)
        return True, f"{self.pet.pet_name} took a restful nap! (+40 Energy, +10 Health)"

    # --- Habit Actions ---
    def complete_habit(self, habit_id: int) -> Tuple[bool, str]:
        for habit in self.habits:
            if habit.id == habit_id:
                if habit.completed:
                    return False, f"'{habit.title}' is already completed today!"
                habit.completed = True
                self.user_coins += habit.reward_coins
                self.pet.gain_exp(habit.reward_exp)
                self.pet.happiness = min(100, self.pet.happiness + 10)
                return True, f"Completed '{habit.title}'! (+{habit.reward_coins} Coins, +{habit.reward_exp} EXP)"
        return False, "Habit not found."

    def get_habit_progress(self) -> Tuple[int, int, float]:
        """Returns (completed_count, total_count, percentage)."""
        total = len(self.habits)
        if total == 0:
            return 0, 0, 0.0
        completed = sum(1 for h in self.habits if h.completed)
        return completed, total, (completed / total) * 100.0

    # --- Shop Actions ---
    def buy_item(self, item_id: int) -> Tuple[bool, str]:
        item = next((i for i in self.shop_catalog if i.id == item_id), None)
        if not item:
            return False, "Item not found in shop."
        if self.user_coins < item.price:
            return False, f"Not enough coins! Need {item.price} coins."

        self.user_coins -= item.price
        if item_id in self.inventory:
            self.inventory[item_id].quantity += 1
        else:
            self.inventory[item_id] = InventoryItem(item_id=item.id, item=item, quantity=1)

        return True, f"Purchased {item.name}! Added to inventory."

    # --- Inventory Actions ---
    def use_item(self, item_id: int) -> Tuple[bool, str]:
        if item_id not in self.inventory or self.inventory[item_id].quantity <= 0:
            return False, "You do not own this item."

        inv_item = self.inventory[item_id]
        item = inv_item.item

        # Check if pet stat is already at maximum before consuming
        pet_name = self.pet.pet_name if self.pet else "Your pet"
        if item.effect_type == "hunger" and self.pet and self.pet.hunger >= 100:
            return False, f"{pet_name} is already full!"

        # Apply effect based on type
        effect_msg = ""
        if item.effect_type == "hunger":
            self.pet.hunger = min(100, self.pet.hunger + item.effect_value)
            effect_msg = f"+{item.effect_value} Hunger"
        elif item.effect_type == "happiness":
            self.pet.happiness = min(100, self.pet.happiness + item.effect_value)
            effect_msg = f"+{item.effect_value} Happiness"
        elif item.effect_type == "energy":
            self.pet.energy = min(100, self.pet.energy + item.effect_value)
            effect_msg = f"+{item.effect_value} Energy"
        elif item.effect_type == "health":
            self.pet.health = min(100, self.pet.health + item.effect_value)
            effect_msg = f"+{item.effect_value} Health"

        self.pet.gain_exp(5)

        inv_item.quantity -= 1
        if inv_item.quantity <= 0:
            del self.inventory[item_id]

        return True, f"Used {item.name}! ({effect_msg}, +5 EXP)"
