"""
Main entry point and Game Application Controller for LittleLife Pygame UI.
Manages screen navigation, event loop, rendering, authentication, and API integration with FastAPI.
"""
import sys
import os
from pathlib import Path
from typing import Callable, Tuple, Dict, Any, Optional, List

# Ensure project root and package directory are in sys.path for direct execution
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

import pygame

try:
    from .theme import (
        WINDOW_WIDTH,
        WINDOW_HEIGHT,
        FPS,
        TITLE,
        COLOR_BG,
        COLOR_NAV_BG,
        COLOR_PRIMARY,
        COLOR_PRIMARY_HOVER,
        COLOR_CARD_BORDER,
        COLOR_TEXT_DARK,
        COLOR_TEXT_MUTED,
        COLOR_TEXT_LIGHT
    )
    from .components import Button, CoinDisplay, NotificationBanner, draw_text
    from .mock_data import MockDataStore, PetState, HabitItem
    from .api_client import APIClient, APIError
    from .screens import (
        PetScreen,
        HabitScreen,
        ShopScreen,
        InventoryScreen,
        LoginScreen
    )
except ImportError:
    from theme import (
        WINDOW_WIDTH,
        WINDOW_HEIGHT,
        FPS,
        TITLE,
        COLOR_BG,
        COLOR_NAV_BG,
        COLOR_PRIMARY,
        COLOR_PRIMARY_HOVER,
        COLOR_CARD_BORDER,
        COLOR_TEXT_DARK,
        COLOR_TEXT_MUTED,
        COLOR_TEXT_LIGHT
    )
    from components import Button, CoinDisplay, NotificationBanner, draw_text
    from mock_data import MockDataStore, PetState, HabitItem
    from api_client import APIClient, APIError
    from screens import (
        PetScreen,
        HabitScreen,
        ShopScreen,
        InventoryScreen,
        LoginScreen
    )


class LittleLifeApp:
    """The central application loop and screen manager."""
    def __init__(self, data_store: Optional[MockDataStore] = None, api_client: Optional[APIClient] = None):
        pygame.init()
        pygame.display.set_caption(TITLE)
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True

        # API Client for backend communication
        self.api = api_client if api_client else APIClient(base_url="http://127.0.0.1:8000")

        # Fallback & local data store (mock or sync target)
        self.data_store = data_store if data_store else MockDataStore()

        # User session info
        self.current_user: Optional[Dict[str, Any]] = None
        self.is_offline_guest: bool = False

        # Notification Banner
        self.notification = NotificationBanner()

        # Coin Display Widget in top right
        coin_w = 124
        coin_x = WINDOW_WIDTH - 20 - coin_w
        self.coin_display = CoinDisplay(x=coin_x, y=16)

        # Active Screen identifier: "login", "pet", "habit", "shop", "inventory"
        self.active_screen_name = "login"

        # Initialize screen instances with callback hooks
        self.screens = {
            "login": LoginScreen(
                on_login_submit=self.handle_login_submit,
                on_continue_offline=self.handle_continue_offline
            ),
            "pet": PetScreen(
                on_feed=self.handle_feed_pet,
                on_play=self.handle_play_pet,
                on_sleep=self.handle_sleep_pet,
                on_create_pet=self.handle_create_pet,
                show_notification=self.show_notification
            ),
            "habit": HabitScreen(
                on_complete_habit=self.handle_complete_habit,
                show_notification=self.show_notification
            ),
            "shop": ShopScreen(
                on_buy_item=self.handle_buy_item,
                show_notification=self.show_notification
            ),
            "inventory": InventoryScreen(
                on_use_item=self.handle_use_item,
                show_notification=self.show_notification
            )
        }

        # Setup top navigation bar buttons
        self._init_nav_buttons()

    def _init_nav_buttons(self):
        """Creates top navigation tabs and session control buttons."""
        tabs = [
            ("pet", "🐾 Pet Companion"),
            ("habit", "📋 Daily Habits"),
            ("shop", "🛒 Store"),
            ("inventory", "🎒 Backpack"),
        ]

        self.nav_buttons: Dict[str, Button] = {}
        nav_x = 160
        nav_y = 16
        tab_width = 120
        tab_gap = 8

        for screen_key, label in tabs:
            btn = Button(
                rect=(nav_x, nav_y, tab_width, 40),
                text=label,
                on_click=lambda sk=screen_key: self.set_screen(sk),
                bg_color=(240, 235, 225),
                hover_color=(230, 224, 212),
                text_color=COLOR_TEXT_DARK,
                font_size=13,
                border_radius=8
            )
            self.nav_buttons[screen_key] = btn
            nav_x += tab_width + tab_gap

        # Logout / Switch Account button - vertically aligned with navigation tabs (y=16, height=40)
        # Positioned neatly to the left of the Coin display with zero overlap
        logout_width = 80
        logout_x = self.coin_display.x - 12 - logout_width
        self.btn_logout = Button(
            rect=(logout_x, nav_y, logout_width, 40),
            text="Log Out",
            on_click=self.handle_logout,
            bg_color=(245, 238, 230),
            hover_color=(235, 225, 215),
            text_color=COLOR_TEXT_MUTED,
            font_size=13,
            border_radius=8
        )

    def set_screen(self, screen_name: str):
        """Switches the active screen view and refreshes screen-specific data if online."""
        if screen_name in self.screens:
            self.active_screen_name = screen_name

            # If moving to Habit screen while authenticated, refresh habits from backend
            if screen_name == "habit" and not self.is_offline_guest and self.api.is_authenticated():
                self._fetch_habits_data()
            elif screen_name == "pet" and not self.is_offline_guest and self.api.is_authenticated():
                self._fetch_pet_data()

    def show_notification(self, message: str, msg_type: str = "info"):
        """Displays temporary toast notification at the top of the UI."""
        self.notification.show(message, msg_type=msg_type, duration=2.8)

    # -------------------------------------------------------------
    # Authentication & API Handlers
    # -------------------------------------------------------------
    def handle_login_submit(self, username: str, password: str) -> Tuple[bool, str]:
        """
        Connects to backend POST /auth/login, fetches GET /auth/me, GET /pets/me, and GET /habits/.
        Replaces hardcoded user/pet/habit data with live backend data.
        """
        try:
            # 1. POST /auth/login
            login_res = self.api.login(username, password)
            token = login_res.get("access_token")
            if not token:
                return False, "Login response missing access token."

            # 2. GET /auth/me
            try:
                user_info = self.api.get_me()
                self.current_user = user_info
                if "coins" in user_info:
                    self.data_store.user_coins = user_info["coins"]
            except APIError as e:
                return False, f"Auth verification failed: {e.message}"

            # 3. GET /pets/me
            self._fetch_pet_data()

            # 4. GET /habits/
            self._fetch_habits_data()

            self.is_offline_guest = False
            self.set_screen("pet")
            self.show_notification(f"Welcome back, {self.current_user.get('username', 'Player')}!", "success")
            return True, "Login successful"

        except APIError as e:
            if e.status_code == 401:
                return False, "Invalid username or password"
            return False, e.message
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"

    def _fetch_pet_data(self):
        """Fetches pet data from GET /pets/me or handles missing/pending pet gracefully."""
        try:
            pet_res = self.api.get_my_pet()
            self.data_store.pet = PetState(
                pet_name=pet_res.get("pet_name", "Pet"),
                level=pet_res.get("level", 1),
                exp=pet_res.get("exp", 0),
                hunger=pet_res.get("hunger", 100),
                happiness=pet_res.get("happiness", 100),
                energy=pet_res.get("energy", 100),
                health=pet_res.get("health", 100)
            )
        except APIError as e:
            if e.status_code == 404:
                # Pet not created yet in backend for this user
                self.data_store.pet = None
            elif e.status_code == 401:
                self.show_notification("Session expired. Please log in again.", "error")
                self.handle_logout()
            else:
                self.show_notification(f"Pet notice: {e.message}", "info")
        except Exception as e:
            self.show_notification(f"Failed to fetch pet: {str(e)}", "error")

    def _fetch_habits_data(self):
        """Fetches daily habit list from GET /habits/ and updates data_store."""
        try:
            habits_res = self.api.get_habits()
            if isinstance(habits_res, list):
                mapped_habits: List[HabitItem] = []
                for h in habits_res:
                    mapped_habits.append(HabitItem(
                        id=h.get("id", 0),
                        title=h.get("title", "Untitled Habit"),
                        description=h.get("description", "") or "",
                        category="Daily",
                        reward_coins=10,  # Defined by backend COINS_REWARD
                        reward_exp=20,    # Defined by backend EXP_REWARD
                        completed=bool(h.get("completed_today", False))
                    ))
                self.data_store.habits = mapped_habits
        except APIError as e:
            if e.status_code == 401:
                self.show_notification("Session expired. Please log in again.", "error")
                self.handle_logout()
            else:
                self.show_notification(f"Habit notice: {e.message}", "info")
        except Exception as e:
            self.show_notification(f"Failed to fetch habits: {str(e)}", "error")

    def handle_continue_offline(self):
        """Allows testing UI offline without requiring a live backend."""
        self.is_offline_guest = True
        self.current_user = {"username": "Guest Explorer", "coins": self.data_store.user_coins}
        self.set_screen("pet")
        self.show_notification("Running in Demo Mode (Mock data)", "info")

    def handle_logout(self):
        """Logs out, clears in-memory session, and returns to login screen."""
        self.api.clear_token()
        self.current_user = None
        self.is_offline_guest = False
        self.set_screen("login")
        self.show_notification("Logged out successfully.", "info")

    # -------------------------------------------------------------
    # Explicit Callback Handlers (Connected to Backend APIs)
    # -------------------------------------------------------------
    def handle_create_pet(self, pet_name: str) -> Tuple[bool, str]:
        """
        Creates a new pet for the user via POST /pets/create.
        Updates state immediately upon creation.
        """
        if self.is_offline_guest:
            # Offline demo creation
            self.data_store.pet = PetState(pet_name=pet_name)
            return True, f"Adopted {pet_name}! (Offline Demo Mode)"

        try:
            res = self.api.create_pet(pet_name=pet_name)
            self.data_store.pet = PetState(
                pet_name=res.get("pet_name", pet_name),
                level=res.get("level", 1),
                exp=res.get("exp", 0),
                hunger=res.get("hunger", 100),
                happiness=res.get("happiness", 100),
                energy=res.get("energy", 100),
                health=res.get("health", 100)
            )
            return True, f"Welcome to the family, {self.data_store.pet.pet_name}!"
        except APIError as e:
            if e.status_code == 401:
                self.handle_logout()
            return False, e.message
        except Exception as e:
            return False, f"Failed to adopt pet: {str(e)}"

    def handle_feed_pet(self) -> Tuple[bool, str]:
        """
        Feed Pet interaction -> POST /care/feed
        Updates hunger while preserving all other stats.
        """
        if self.data_store.pet is None:
            return False, "No active pet to feed."

        if self.is_offline_guest:
            return self.data_store.feed_pet()

        try:
            res = self.api.care_feed()
            new_hunger = res.get("hunger", min(100, self.data_store.pet.hunger + 30))
            self.data_store.pet.hunger = new_hunger
            return True, f"Fed {self.data_store.pet.pet_name}! (Hunger: {new_hunger}/100)"
        except APIError as e:
            if e.status_code == 401:
                self.handle_logout()
            return False, e.message
        except Exception as e:
            return False, f"Feed error: {str(e)}"

    def handle_play_pet(self) -> Tuple[bool, str]:
        """
        Play with Pet interaction -> POST /care/play
        Updates happiness and energy. Handles 400 'Not enough energy'.
        """
        if self.data_store.pet is None:
            return False, "No active pet to play with."

        if self.is_offline_guest:
            return self.data_store.play_with_pet()

        try:
            res = self.api.care_play()
            new_happiness = res.get("happiness", min(100, self.data_store.pet.happiness + 20))
            new_energy = res.get("energy", max(0, self.data_store.pet.energy - 20))
            self.data_store.pet.happiness = new_happiness
            self.data_store.pet.energy = new_energy
            return True, f"Played with {self.data_store.pet.pet_name}! (+20 Joy, -20 Energy)"
        except APIError as e:
            if e.status_code == 401:
                self.handle_logout()
            return False, e.message
        except Exception as e:
            return False, f"Play error: {str(e)}"

    def handle_sleep_pet(self) -> Tuple[bool, str]:
        """
        Pet Rest interaction -> POST /care/rest
        Updates energy while preserving other stats.
        """
        if self.data_store.pet is None:
            return False, "No active pet to put to sleep."

        if self.is_offline_guest:
            return self.data_store.pet_sleep()

        try:
            res = self.api.care_rest()
            new_energy = res.get("energy", min(100, self.data_store.pet.energy + 30))
            self.data_store.pet.energy = new_energy
            return True, f"{self.data_store.pet.pet_name} rested peacefully! (Energy: {new_energy}/100)"
        except APIError as e:
            if e.status_code == 401:
                self.handle_logout()
            return False, e.message
        except Exception as e:
            return False, f"Rest error: {str(e)}"

    def handle_complete_habit(self, habit_id: int) -> Tuple[bool, str]:
        """
        Complete Habit interaction -> POST /habits/{habit_id}/complete
        Updates habit completion status, User coins, Pet EXP, and Pet Level.
        """
        if self.is_offline_guest:
            return self.data_store.complete_habit(habit_id)

        try:
            res = self.api.complete_habit(habit_id)

            # Update habit completion status locally
            for h in self.data_store.habits:
                if h.id == habit_id:
                    h.completed = True

            # Synchronize Coins
            if "total_coins" in res:
                self.data_store.user_coins = res["total_coins"]

            # Synchronize Pet EXP & Level
            if self.data_store.pet:
                if "pet_exp" in res:
                    self.data_store.pet.exp = res["pet_exp"]
                if "pet_level" in res:
                    self.data_store.pet.level = res["pet_level"]

            leveled_up = res.get("leveled_up", False)
            coins_earned = res.get("coins_earned", 10)
            exp_earned = res.get("exp_earned", 20)

            msg = f"Completed habit! (+{coins_earned} Coins, +{exp_earned} EXP)"
            if leveled_up and self.data_store.pet:
                msg += f" 🎉 {self.data_store.pet.pet_name} leveled up to Level {self.data_store.pet.level}!"

            return True, msg
        except APIError as e:
            if e.status_code == 401:
                self.handle_logout()
            elif e.status_code == 409:
                # Mark as completed locally if backend says it was already completed today
                for h in self.data_store.habits:
                    if h.id == habit_id:
                        h.completed = True
            return False, e.message
        except Exception as e:
            return False, f"Habit completion error: {str(e)}"

    def handle_buy_item(self, item_id: int) -> Tuple[bool, str]:
        """
        Buy Shop Item interaction (Local Simulation).
        """
        return self.data_store.buy_item(item_id)

    def handle_use_item(self, item_id: int) -> Tuple[bool, str]:
        """
        Use Inventory Item interaction (Local Simulation).
        """
        return self.data_store.use_item(item_id)

    # -------------------------------------------------------------
    # Main Event Loop & Rendering
    # -------------------------------------------------------------
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return

            if self.active_screen_name == "login":
                self.screens["login"].handle_event(event)
            else:
                for btn in self.nav_buttons.values():
                    btn.handle_event(event)

                self.btn_logout.handle_event(event)

                current_screen = self.screens.get(self.active_screen_name)
                if current_screen:
                    if self.active_screen_name == "pet":
                        current_screen.handle_event(event, pet_exists=(self.data_store.pet is not None))
                    else:
                        current_screen.handle_event(event)

    def update(self, dt: float):
        self.notification.update(dt)
        current_screen = self.screens.get(self.active_screen_name)
        if current_screen:
            if self.active_screen_name == "pet":
                current_screen.update(dt, pet_exists=(self.data_store.pet is not None))
            else:
                current_screen.update(dt)

    def render_top_bar(self):
        """Renders the top navigation header and status indicators."""
        header_rect = pygame.Rect(0, 0, WINDOW_WIDTH, 72)
        pygame.draw.rect(self.screen, COLOR_NAV_BG, header_rect)
        pygame.draw.line(self.screen, COLOR_CARD_BORDER, (0, 72), (WINDOW_WIDTH, 72), 1)

        # Brand Logo / App Title
        draw_text(self.screen, "LittleLife", (24, 23), font_size=23, color=COLOR_PRIMARY, bold=True)

        # Navigation Tabs
        for screen_key, btn in self.nav_buttons.items():
            if screen_key == self.active_screen_name:
                btn.bg_color = COLOR_PRIMARY
                btn.hover_color = COLOR_PRIMARY_HOVER
                btn.text_color = COLOR_TEXT_LIGHT
            else:
                btn.bg_color = (248, 244, 237)
                btn.hover_color = (235, 230, 222)
                btn.text_color = COLOR_TEXT_DARK

            btn.render(self.screen)

        # User Profile Indicator & Logout Button
        if self.current_user:
            uname = self.current_user.get("username", "User")
            # Render username text centered right above the Log Out button with clean margin
            draw_text(self.screen, f"👤 {uname}", (self.btn_logout.rect.centerx, 8), font_size=11, color=COLOR_TEXT_DARK, bold=True, align="center")
            self.btn_logout.render(self.screen)

        # Coin Display Widget
        self.coin_display.render(self.screen, self.data_store.user_coins)

    def render(self):
        if self.active_screen_name == "login":
            self.screens["login"].render(self.screen)
        else:
            self.screen.fill(COLOR_BG)
            self.render_top_bar()

            if self.active_screen_name == "pet":
                self.screens["pet"].render(self.screen, self.data_store.pet)
            elif self.active_screen_name == "habit":
                comp, tot, pct = self.data_store.get_habit_progress()
                self.screens["habit"].render(self.screen, self.data_store.habits, comp, tot, pct)
            elif self.active_screen_name == "shop":
                self.screens["shop"].render(self.screen, self.data_store.shop_catalog, self.data_store.user_coins)
            elif self.active_screen_name == "inventory":
                self.screens["inventory"].render(self.screen, self.data_store.inventory)

        self.notification.render(self.screen, center_x=WINDOW_WIDTH // 2, top_y=84)
        pygame.display.flip()

    def run(self):
        """Runs the main game loop."""
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self.handle_events()
            self.update(dt)
            self.render()

        pygame.quit()
        sys.exit()


def main():
    """Application entrypoint."""
    app = LittleLifeApp()
    app.run()


if __name__ == "__main__":
    main()
