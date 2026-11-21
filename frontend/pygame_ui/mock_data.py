"""
Kho dữ liệu mock và các domain model cho prototype UI LittleLife.
Lưu trạng thái cục bộ và mô phỏng các hành động trong game (cho ăn, chơi, ngủ, hoàn thành habit, mua, sử dụng).
"""
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional

# Các giá trị chăm sóc khớp với backend/constants.py để Online và Demo Mode hoạt động giống nhau.
FEED_HUNGER_GAIN = 15
PLAY_HUNGER_COST = 10
PLAY_ENERGY_COST = 10
PLAY_HAPPINESS_GAIN = 15
SLEEP_ENERGY_GAIN = 30
SLEEP_HEALTH_GAIN = 5
STAT_MAX = 100


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
    item_type: str        # "food", "toy", "medicine", "potion", "comfort"
    price: int
    effect_type: str      # "hunger", "happiness", "energy", "health"
    effect_value: int
    description: str
    secondary_effect_type: Optional[str] = None
    secondary_effect_value: int = 0

    def get_effects(self) -> List[Tuple[str, int]]:
        """Trả về hiệu ứng chính kèm hiệu ứng phụ tùy chọn."""
        effects: List[Tuple[str, int]] = []

        if self.effect_type and self.effect_value > 0:
            effects.append((self.effect_type, self.effect_value))

        if self.secondary_effect_type and self.secondary_effect_value > 0:
            effects.append((self.secondary_effect_type, self.secondary_effect_value))

        return effects

    def effect_summary(self) -> str:
        return "  ".join(
            f"+{value} {effect_type.capitalize()}"
            for effect_type, value in self.get_effects()
        )


@dataclass
class InventoryItem:
    item_id: int
    item: ShopItem
    quantity: int


class MockDataStore:
    """Kho dữ liệu mock tập trung, đại diện cho trạng thái của backend."""
    def __init__(self):
        self.user_coins: int = 150
        self.pet: PetState = PetState()

        self.habits: List[HabitItem] = [
            HabitItem(
                id=1,
                title="Morning Water",
                description="Drink 500ml of clean warm water after waking up",
                category="Health",
                reward_coins=10,
                reward_exp=20,
                completed=False
            ),
            HabitItem(
                id=2,
                title="30-min Reading",
                description="Read a programming book or inspiring novel",
                category="Learning",
                reward_coins=10,
                reward_exp=20,
                completed=True
            ),
            HabitItem(
                id=3,
                title="Afternoon Walk",
                description="Get some fresh air and walk for at least 15 minutes",
                category="Fitness",
                reward_coins=10,
                reward_exp=20,
                completed=False
            ),
            HabitItem(
                id=4,
                title="Sleep before 11 PM",
                description="Wind down screen time and get 8 hours of sleep",
                category="Rest",
                reward_coins=10,
                reward_exp=20,
                completed=False
            ),
        ]

        # Danh mục item đang bán trong cửa hàng
        self.shop_catalog: List[ShopItem] = [
            ShopItem(
                id=101,
                name="Crispy Biscuit",
                item_type="food",
                price=15,
                effect_type="hunger",
                effect_value=30,
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
                effect_value=30,
                description="Soothing natural remedy to restore pet vitality."
            ),
            ShopItem(
                id=105,
                name="Energy Elixir",
                item_type="potion",
                price=50,
                effect_type="energy",
                effect_value=30,
                description="Sparkling drink that instantly boosts pet stamina."
            ),
            ShopItem(
                id=106,
                name="Cozy Pillow",
                item_type="comfort",
                price=40,
                effect_type="energy",
                effect_value=20,
                secondary_effect_type="health",
                secondary_effect_value=10,
                description="A soft, warm pillow that restores Energy and Health."
            ),
        ]

        # Túi đồ khởi đầu của người dùng
        self.inventory: Dict[int, InventoryItem] = {
            101: InventoryItem(item_id=101, item=self.shop_catalog[0], quantity=3),
            103: InventoryItem(item_id=103, item=self.shop_catalog[2], quantity=1),
        }

    # --- Hành động với Pet ---
    # Hiệu ứng khớp với các endpoint /care của FastAPI để cả hai chế độ hoạt động giống nhau.
    def feed_pet(self) -> Tuple[bool, str]:
        if self.pet.hunger >= STAT_MAX:
            return False, f"{self.pet.pet_name} is already full!"
        self.pet.hunger = min(STAT_MAX, self.pet.hunger + FEED_HUNGER_GAIN)
        return True, f"Fed {self.pet.pet_name}! (Hunger: {self.pet.hunger}/100)"

    def play_with_pet(self) -> Tuple[bool, str]:
        if self.pet.hunger < PLAY_HUNGER_COST:
            return False, f"{self.pet.pet_name} is too hungry to play! Feed them first."
        if self.pet.energy < PLAY_ENERGY_COST:
            return False, f"{self.pet.pet_name} is too tired to play! Let them rest."

        self.pet.hunger = max(0, self.pet.hunger - PLAY_HUNGER_COST)
        self.pet.energy = max(0, self.pet.energy - PLAY_ENERGY_COST)
        self.pet.happiness = min(STAT_MAX, self.pet.happiness + PLAY_HAPPINESS_GAIN)

        return True, (
            f"Played with {self.pet.pet_name}! "
            f"(Happiness: {self.pet.happiness}/100, Energy: {self.pet.energy}/100, "
            f"Hunger: {self.pet.hunger}/100)"
        )

    def pet_sleep(self) -> Tuple[bool, str]:
        if self.pet.energy >= STAT_MAX and self.pet.health >= STAT_MAX:
            return False, f"{self.pet.pet_name} is already fully rested and healthy!"

        self.pet.energy = min(STAT_MAX, self.pet.energy + SLEEP_ENERGY_GAIN)
        self.pet.health = min(STAT_MAX, self.pet.health + SLEEP_HEALTH_GAIN)

        return True, (
            f"{self.pet.pet_name} rested peacefully! "
            f"(Energy: {self.pet.energy}/100, Health: {self.pet.health}/100)"
        )

    # --- Hành động với Habit ---
    def add_habit(self, title: str, description: str = "") -> Tuple[bool, str]:
        title = (title or "").strip()
        if not title:
            return False, "Habit title cannot be empty."
        new_id = max((habit.id for habit in self.habits), default=0) + 1
        self.habits.append(
            HabitItem(
                id=new_id,
                title=title,
                description=(description or "").strip(),
                category="Daily",
                reward_coins=10,
                reward_exp=20,
                completed=False
            )
        )
        return True, f"Added habit '{title}'!"

    def complete_habit(self, habit_id: int) -> Tuple[bool, str]:
        for habit in self.habits:
            if habit.id == habit_id:
                if habit.completed:
                    return False, f"'{habit.title}' is already completed today!"
                habit.completed = True
                self.user_coins += habit.reward_coins
                self.pet.gain_exp(habit.reward_exp)
                return True, f"Completed '{habit.title}'! (+{habit.reward_coins} Coins, +{habit.reward_exp} EXP)"
        return False, "Habit not found."

    def delete_habit(self, habit_id: int) -> Tuple[bool, str]:
        """Xóa habit trong Demo Mode; Coin/EXP đã nhận vẫn được giữ nguyên."""
        for index, habit in enumerate(self.habits):
            if habit.id == habit_id:
                self.habits.pop(index)
                return True, f"Deleted habit '{habit.title}'."
        return False, "Habit not found."

    def get_habit_progress(self) -> Tuple[int, int, float]:
        """Trả về (số đã hoàn thành, tổng số, phần trăm)."""
        total = len(self.habits)
        if total == 0:
            return 0, 0, 0.0
        completed = sum(1 for h in self.habits if h.completed)
        return completed, total, (completed / total) * 100.0

    # --- Hành động với Store ---
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

    # --- Hành động với Backpack ---
    STAT_LABELS = {
        "hunger": "Hunger",
        "happiness": "Happiness",
        "energy": "Energy",
        "health": "Health",
    }

    def use_item(self, item_id: int) -> Tuple[bool, str]:
        if item_id not in self.inventory or self.inventory[item_id].quantity <= 0:
            return False, "You do not own this item."

        if self.pet is None:
            return False, "You need to adopt a pet before using items."

        inv_item = self.inventory[item_id]
        item = inv_item.item
        effects = item.get_effects()

        if not effects:
            return False, f"{item.name} has no usable effect."

        for effect_type, _ in effects:
            if effect_type not in self.STAT_LABELS:
                return False, f"{item.name} has an unsupported effect."

        pet_name = self.pet.pet_name
        applied: List[Tuple[str, int]] = []
        full_labels: List[str] = []

        # Item ảnh hưởng nhiều chỉ số vẫn dùng được khi còn ít nhất một chỉ số có thể tăng.
        for effect_type, value in effects:
            current_value = getattr(self.pet, effect_type)

            if current_value >= STAT_MAX:
                full_labels.append(self.STAT_LABELS[effect_type])
                continue

            new_value = min(STAT_MAX, current_value + value)
            setattr(self.pet, effect_type, new_value)
            applied.append((effect_type, new_value - current_value))

        if not applied:
            labels = " and ".join(full_labels)
            verb = "is" if len(full_labels) == 1 else "are"
            return False, f"{pet_name}'s {labels} {verb} already full!"

        inv_item.quantity -= 1
        if inv_item.quantity <= 0:
            del self.inventory[item_id]

        summary = ", ".join(
            f"+{value} {self.STAT_LABELS[effect_type]}"
            for effect_type, value in applied
        )
        return True, f"Used {item.name}! ({summary})"
