"""
Screens package for LittleLife Pygame UI prototype.
"""
try:
    from .pet_screen import PetScreen
    from .habit_screen import HabitScreen
    from .shop_screen import ShopScreen
    from .inventory_screen import InventoryScreen
    from .login_screen import LoginScreen
except ImportError:
    from screens.pet_screen import PetScreen
    from screens.habit_screen import HabitScreen
    from screens.shop_screen import ShopScreen
    from screens.inventory_screen import InventoryScreen
    from screens.login_screen import LoginScreen

__all__ = [
    "PetScreen",
    "HabitScreen",
    "ShopScreen",
    "InventoryScreen",
    "LoginScreen",
]
