"""
Điểm khởi chạy chính và bộ điều khiển ứng dụng game cho LittleLife Pygame UI.
Quản lý điều hướng màn hình, vòng lặp sự kiện, render, xác thực và tích hợp API với FastAPI.
"""
import sys
import os
from pathlib import Path
from typing import Callable, Tuple, Dict, Any, Optional, List

# Đảm bảo thư mục gốc dự án và thư mục package có trong sys.path khi chạy trực tiếp
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
    from .mock_data import (
        MockDataStore,
        PetState,
        HabitItem,
        ShopItem,
        InventoryItem,
    )
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
    from mock_data import (
        MockDataStore,
        PetState,
        HabitItem,
        ShopItem,
        InventoryItem,
    )
    from api_client import APIClient, APIError
    from screens import (
        PetScreen,
        HabitScreen,
        ShopScreen,
        InventoryScreen,
        LoginScreen
    )


class LittleLifeApp:
    """Vòng lặp ứng dụng trung tâm và bộ quản lý màn hình."""
    def __init__(self, data_store: Optional[MockDataStore] = None, api_client: Optional[APIClient] = None):
        pygame.init()
        pygame.display.set_caption(TITLE)
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))

        # Bật nhận văn bản đã hợp thành từ IME (VNI/Telex) qua TEXTINPUT.
        # Nếu driver không hỗ trợ (headless/dummy), bỏ qua an toàn.
        try:
            pygame.key.start_text_input()
        except pygame.error:
            pass

        self.clock = pygame.time.Clock()
        self.running = True

        # API Client dùng để giao tiếp với backend
        self.api = api_client if api_client else APIClient(
            base_url=os.getenv("LITTLELIFE_API_URL", "http://127.0.0.1:8000")
        )

        # Kho dữ liệu cục bộ & dự phòng (mock hoặc đích đồng bộ)
        self.data_store = data_store if data_store else MockDataStore()

        # Thông tin phiên của người dùng
        self.current_user: Optional[Dict[str, Any]] = None
        self.is_offline_guest: bool = False

        # Banner thông báo
        self.notification = NotificationBanner()

        # Widget hiển thị Coin ở góc trên bên phải
        coin_w = 124
        coin_x = WINDOW_WIDTH - 20 - coin_w
        self.coin_display = CoinDisplay(x=coin_x, y=16)

        # Mã màn hình đang hoạt động: "login", "pet", "habit", "shop", "inventory"
        self.active_screen_name = "login"

        # Khởi tạo các instance màn hình kèm các callback
        self.screens = {
            "login": LoginScreen(
                on_login_submit=self.handle_login_submit,
                on_continue_offline=self.handle_continue_offline,
                on_register_submit=self.handle_register_submit
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
                on_create_habit=self.handle_create_habit,
                on_delete_habit=self.handle_delete_habit,
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

        # Thiết lập các nút trên thanh điều hướng phía trên
        self._init_nav_buttons()

    def _init_nav_buttons(self):
        """Tạo các tab điều hướng phía trên và các nút điều khiển phiên."""
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

        # Nút Đăng xuất / Đổi tài khoản - căn thẳng hàng dọc với các tab điều hướng (y=16, height=40)
        # Đặt gọn gàng bên trái phần hiển thị Coin, không chồng lấn
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
        """Chuyển màn hình đang hiển thị và làm mới dữ liệu riêng của màn hình nếu đang online."""
        if screen_name in self.screens:
            self.active_screen_name = screen_name

            # Xóa trạng thái UI tạm (khóa button đang xử lý, vị trí cuộn) còn sót lại
            # từ lần truy cập trước hoặc từ lần chuyển phiên.
            screen = self.screens.get(screen_name)
            if screen is not None and hasattr(screen, "on_show"):
                screen.on_show()

            if self.is_offline_guest or not self.api.is_authenticated():
                return

            # Ở Online Mode, dữ liệu luôn được làm mới từ backend gốc mỗi khi
            # vào màn hình, nên các giá trị không bị cũ khi chuyển tab.
            if screen_name == "habit":
                self._fetch_habits_data()
            elif screen_name == "pet":
                self._fetch_pet_data()
            elif screen_name == "shop":
                self._fetch_store_data()
                self._fetch_inventory_data()
            elif screen_name == "inventory":
                self._fetch_inventory_data()

    def show_notification(self, message: str, msg_type: str = "info"):
        """Hiển thị thông báo toast tạm thời ở phía trên UI."""
        self.notification.show(message, msg_type=msg_type, duration=2.8)

    # -------------------------------------------------------------
    # Xác thực & các handler API
    # -------------------------------------------------------------
    def handle_login_submit(self, username: str, password: str) -> Tuple[bool, str]:
        """
        Kết nối tới POST /auth/login của backend, sau đó tải hồ sơ, pet, habit,
        catalog của Store và Backpack chính thức của người chơi.
        """
        try:
            # 1. Gọi POST /auth/login
            login_res = self.api.login(username, password)
            token = login_res.get("access_token")
            if not token:
                self.api.clear_token()
                return False, "Login response missing access token."

            # 2. Gọi GET /auth/me
            try:
                user_info = self.api.get_me()
            except APIError as e:
                self.api.clear_token()
                return False, f"Auth verification failed: {e.message}"

            # Xóa trạng thái demo / tài khoản trước đó trước khi tải dữ liệu từ backend.
            self._reset_local_state()
            self.current_user = user_info
            self.data_store.user_coins = user_info.get("coins", 0)

            # 3. Gọi GET /pets/me, GET /habits/, GET /store/items, GET /inventory/
            self._fetch_pet_data()
            self._fetch_habits_data()
            self._fetch_store_data()
            self._fetch_inventory_data()

            # Lỗi 401 trong lần đồng bộ đầu sẽ đăng xuất phiên; không tiếp tục
            # vào game với token đã bị xóa.
            if not self.api.is_authenticated() or self.current_user is None:
                return False, "Session could not be verified. Please log in again."

            # Dữ liệu đã được tải, nên chuyển thẳng tới màn hình pet.
            self.active_screen_name = "pet"
            self.screens["login"].reset_form()
            self.show_notification(f"Welcome back, {self.current_user.get('username', 'Player')}!", "success")
            return True, "Login successful"

        except APIError as e:
            if e.status_code == 401:
                return False, "Invalid username or password"
            return False, e.message
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"

    def handle_register_submit(self, username: str, email: str, password: str) -> Tuple[bool, str]:
        """
        Đăng ký tài khoản mới (POST /auth/register) và đăng nhập ngay sau đó.
        """
        try:
            self.api.register(username, email, password)
        except APIError as e:
            return False, e.message
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"

        success, message = self.handle_login_submit(username, password)
        if success:
            self.show_notification("Account created! Welcome to LittleLife.", "success")
            return True, "Account created"
        return False, message

    def _reset_local_state(self):
        """Thay trạng thái chơi cục bộ bằng một kho demo mới tinh.

        Dữ liệu online được tải từ backend ngay sau thao tác này, nên cả giá trị
        mock cũ lẫn giá trị của tài khoản trước đều không thể tồn tại qua một phiên.
        """
        self.data_store = MockDataStore()
        self.current_user = None
        self.is_offline_guest = False

    def _handle_api_error(self, error: APIError, context: str):
        """Nơi tập trung phản hồi lỗi API (phiên hết hạn hoặc thông báo tham khảo)."""
        if error.status_code == 401:
            self.show_notification("Session expired. Please log in again.", "error")
            self.handle_logout()
        else:
            self.show_notification(f"{context}: {error.message}", "info")

    @staticmethod
    def _map_shop_items(entries: Any) -> List[ShopItem]:
        """Chuyển dữ liệu catalog từ backend sang model ShopItem của UI."""
        mapped: List[ShopItem] = []
        for entry in entries or []:
            try:
                mapped.append(
                    ShopItem(
                        id=int(entry.get("id", 0)),
                        name=entry.get("name", "Item"),
                        item_type=entry.get("item_type", "food"),
                        price=int(entry.get("price", 0)),
                        effect_type=entry.get("effect_type", "hunger"),
                        effect_value=int(entry.get("effect_value", 0)),
                        description=entry.get("description", "") or "",
                        secondary_effect_type=entry.get("secondary_effect_type"),
                        secondary_effect_value=int(entry.get("secondary_effect_value") or 0)
                    )
                )
            except (TypeError, ValueError, AttributeError):
                continue
        return mapped

    def _apply_inventory(self, entries: Any):
        """Thay Backpack cục bộ bằng dữ liệu inventory từ backend."""
        inventory: Dict[int, InventoryItem] = {}
        for entry in entries or []:
            try:
                item_id = int(entry.get("item_id", entry.get("id", 0)))
                quantity = int(entry.get("quantity", 0))
                if item_id <= 0 or quantity <= 0:
                    continue

                inventory[item_id] = InventoryItem(
                    item_id=item_id,
                    item=ShopItem(
                        id=item_id,
                        name=entry.get("name", "Item"),
                        item_type=entry.get("item_type", "food"),
                        price=int(entry.get("price", 0)),
                        effect_type=entry.get("effect_type", "hunger"),
                        effect_value=int(entry.get("effect_value", 0)),
                        description=entry.get("description", "") or "",
                        secondary_effect_type=entry.get("secondary_effect_type"),
                        secondary_effect_value=int(entry.get("secondary_effect_value") or 0)
                    ),
                    quantity=quantity
                )
            except (TypeError, ValueError, AttributeError):
                continue

        self.data_store.inventory = inventory

    def _apply_pet_snapshot(self, pet_data: Any):
        """Áp dụng snapshot pet chính thức do endpoint hành động trả về."""
        if not isinstance(pet_data, dict) or not pet_data.get("pet_name"):
            return

        pet = self.data_store.pet
        if pet is None:
            self.data_store.pet = PetState(
                pet_name=pet_data.get("pet_name", "Pet"),
                level=pet_data.get("level", 1),
                exp=pet_data.get("exp", 0),
                exp_to_next_level=pet_data.get("exp_to_next_level", 100),
                hunger=pet_data.get("hunger", 100),
                happiness=pet_data.get("happiness", 100),
                energy=pet_data.get("energy", 100),
                health=pet_data.get("health", 100)
            )
            return

        pet.pet_name = pet_data.get("pet_name", pet.pet_name)
        pet.exp_to_next_level = pet_data.get("exp_to_next_level", pet.exp_to_next_level)
        for field in ("level", "exp", "hunger", "happiness", "energy", "health"):
            if field in pet_data:
                setattr(pet, field, pet_data[field])

    def _fetch_wallet(self):
        """Làm mới số dư Coin và tên người dùng chính thức."""
        try:
            user_info = self.api.get_me()
            self.current_user = user_info
            self.data_store.user_coins = user_info.get("coins", self.data_store.user_coins)
        except APIError as e:
            self._handle_api_error(e, "Profile")
        except Exception as e:
            self.show_notification(f"Failed to refresh wallet: {str(e)}", "error")

    def _fetch_pet_data(self):
        """Lấy dữ liệu pet từ GET /pets/me hoặc xử lý nhẹ nhàng khi chưa có pet."""
        try:
            pet_res = self.api.get_my_pet()
            self.data_store.pet = PetState(
                pet_name=pet_res.get("pet_name", "Pet"),
                level=pet_res.get("level", 1),
                exp=pet_res.get("exp", 0),
                exp_to_next_level=pet_res.get("exp_to_next_level", 100),
                hunger=pet_res.get("hunger", 100),
                happiness=pet_res.get("happiness", 100),
                energy=pet_res.get("energy", 100),
                health=pet_res.get("health", 100)
            )
        except APIError as e:
            if e.status_code == 404:
                # Người dùng này chưa tạo pet trong backend
                self.data_store.pet = None
            else:
                self._handle_api_error(e, "Pet")
        except Exception as e:
            self.show_notification(f"Failed to fetch pet: {str(e)}", "error")

    def _fetch_habits_data(self):
        """Lấy danh sách habit hằng ngày từ GET /habits/ và cập nhật data_store."""
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
                        reward_coins=h.get("reward_coins", 10),
                        reward_exp=h.get("reward_exp", 20),
                        completed=bool(h.get("completed_today", False))
                    ))
                self.data_store.habits = mapped_habits
        except APIError as e:
            self._handle_api_error(e, "Habit")
        except Exception as e:
            self.show_notification(f"Failed to fetch habits: {str(e)}", "error")

    def _fetch_store_data(self):
        """Lấy catalog của Store và số dư Coin chính thức."""
        try:
            store_res = self.api.get_store_items()
            if isinstance(store_res, dict):
                if "coins" in store_res:
                    self.data_store.user_coins = store_res["coins"]
                self.data_store.shop_catalog = self._map_shop_items(store_res.get("items", []))
        except APIError as e:
            self._handle_api_error(e, "Store")
        except Exception as e:
            self.show_notification(f"Failed to fetch store: {str(e)}", "error")

    def _fetch_inventory_data(self):
        """Lấy các item người chơi đang sở hữu và số dư Coin chính thức."""
        try:
            inventory_res = self.api.get_inventory()
            if isinstance(inventory_res, dict):
                if "coins" in inventory_res:
                    self.data_store.user_coins = inventory_res["coins"]
                self._apply_inventory(inventory_res.get("items", []))
        except APIError as e:
            self._handle_api_error(e, "Inventory")
        except Exception as e:
            self.show_notification(f"Failed to fetch inventory: {str(e)}", "error")

    def handle_continue_offline(self):
        """Cho phép thử UI offline mà không cần backend đang chạy."""
        self.api.clear_token()
        self._reset_local_state()
        self.is_offline_guest = True
        self.current_user = {"username": "Guest Explorer", "coins": self.data_store.user_coins}
        self.set_screen("pet")
        self.show_notification("Running in Demo Mode (Mock data)", "info")

    def handle_logout(self):
        """Đăng xuất, xóa phiên trong bộ nhớ và quay về màn hình đăng nhập."""
        self.api.clear_token()
        self._reset_local_state()
        self.screens["login"].reset_form()
        self.set_screen("login")
        self.show_notification("Logged out successfully.", "info")

    # -------------------------------------------------------------
    # Các handler callback tường minh (kết nối với API của backend)
    # -------------------------------------------------------------
    def handle_create_pet(self, pet_name: str) -> Tuple[bool, str]:
        """
        Tạo pet mới cho người dùng qua POST /pets/create.
        Cập nhật trạng thái ngay sau khi tạo.
        """
        if self.is_offline_guest:
            # Tạo pet trong chế độ demo offline
            self.data_store.pet = PetState(pet_name=pet_name)
            return True, f"Adopted {pet_name}! (Offline Demo Mode)"

        try:
            res = self.api.create_pet(pet_name=pet_name)
            self.data_store.pet = PetState(
                pet_name=res.get("pet_name", pet_name),
                level=res.get("level", 1),
                exp=res.get("exp", 0),
                exp_to_next_level=res.get("exp_to_next_level", 100),
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
        Hành động cho Pet ăn -> POST /care/feed
        Cập nhật hunger mà vẫn giữ nguyên các chỉ số khác.
        """
        if self.data_store.pet is None:
            return False, "No active pet to feed."

        if self.is_offline_guest:
            return self.data_store.feed_pet()

        try:
            res = self.api.care_feed()
            self._apply_pet_snapshot(res.get("pet"))
            pet = self.data_store.pet
            new_hunger = res.get("hunger", min(100, pet.hunger + 15))
            pet.hunger = new_hunger
            return True, f"Fed {pet.pet_name}! (Hunger: {new_hunger}/100)"
        except APIError as e:
            if e.status_code == 401:
                self.handle_logout()
            return False, e.message
        except Exception as e:
            return False, f"Feed error: {str(e)}"

    def handle_play_pet(self) -> Tuple[bool, str]:
        """
        Hành động chơi với Pet -> POST /care/play
        Cập nhật happiness và energy. Xử lý lỗi 400 'Not enough energy'.
        """
        if self.data_store.pet is None:
            return False, "No active pet to play with."

        if self.is_offline_guest:
            return self.data_store.play_with_pet()

        try:
            res = self.api.care_play()
            self._apply_pet_snapshot(res.get("pet"))
            pet = self.data_store.pet
            new_happiness = res.get("happiness", min(100, pet.happiness + 15))
            new_energy = res.get("energy", max(0, pet.energy - 10))
            new_hunger = res.get("hunger", max(0, pet.hunger - 10))
            pet.happiness = new_happiness
            pet.energy = new_energy
            pet.hunger = new_hunger
            return True, (
                f"Played with {pet.pet_name}! "
                f"(Happiness: {new_happiness}/100, Energy: {new_energy}/100, "
                f"Hunger: {new_hunger}/100)"
            )
        except APIError as e:
            if e.status_code == 401:
                self.handle_logout()
            return False, e.message
        except Exception as e:
            return False, f"Play error: {str(e)}"

    def handle_sleep_pet(self) -> Tuple[bool, str]:
        """
        Hành động cho Pet nghỉ ngơi -> POST /care/rest
        Cập nhật energy mà vẫn giữ nguyên các chỉ số khác.
        """
        if self.data_store.pet is None:
            return False, "No active pet to put to sleep."

        if self.is_offline_guest:
            return self.data_store.pet_sleep()

        try:
            res = self.api.care_rest()
            self._apply_pet_snapshot(res.get("pet"))
            pet = self.data_store.pet
            new_energy = res.get("energy", min(100, pet.energy + 30))
            new_health = res.get("health", min(100, pet.health + 5))
            pet.energy = new_energy
            pet.health = new_health
            return True, (
                f"{pet.pet_name} rested peacefully! "
                f"(Energy: {new_energy}/100, Health: {new_health}/100)"
            )
        except APIError as e:
            if e.status_code == 401:
                self.handle_logout()
            return False, e.message
        except Exception as e:
            return False, f"Rest error: {str(e)}"

    def handle_create_habit(self, title: str, description: str = "") -> Tuple[bool, str]:
        """
        Hành động tạo Habit -> POST /habits/create (mô phỏng cục bộ khi offline).
        """
        if self.is_offline_guest:
            return self.data_store.add_habit(title, description)

        try:
            res = self.api.create_habit(title, (description or "").strip() or None)
            self._fetch_habits_data()
            return True, f"Added habit '{res.get('title', title)}'!"
        except APIError as e:
            if e.status_code == 401:
                self.handle_logout()
            return False, e.message
        except Exception as e:
            return False, f"Could not create habit: {str(e)}"

    def handle_delete_habit(self, habit_id: int) -> Tuple[bool, str]:
        """
        Hành động xóa Habit -> DELETE /habits/{habit_id} (mô phỏng cục bộ khi offline).
        Chỉ xóa khỏi danh sách UI sau khi backend xác nhận thành công.
        """
        if self.is_offline_guest:
            return self.data_store.delete_habit(habit_id)

        try:
            res = self.api.delete_habit(habit_id)
        except APIError as e:
            if e.status_code == 401:
                self.handle_logout()
            elif e.status_code == 404:
                # Habit đã bị xóa ở nơi khác hoặc không thuộc user hiện tại:
                # đồng bộ lại danh sách theo trạng thái thật của backend.
                self._fetch_habits_data()
            return False, e.message
        except Exception as e:
            return False, f"Could not delete habit: {str(e)}"

        # Backend đã xóa thành công: bỏ khỏi danh sách cục bộ rồi tải lại
        # danh sách chính thức để đồng bộ với server.
        self.data_store.habits = [h for h in self.data_store.habits if h.id != habit_id]
        self._fetch_habits_data()

        return True, f"Deleted habit '{res.get('habit_title', '')}'."

    def handle_complete_habit(self, habit_id: int) -> Tuple[bool, str]:
        """
        Hành động hoàn thành Habit -> POST /habits/{habit_id}/complete
        Cập nhật trạng thái hoàn thành habit, Coin của người dùng, EXP và Level của Pet.
        """
        if self.is_offline_guest:
            return self.data_store.complete_habit(habit_id)

        try:
            res = self.api.complete_habit(habit_id)

            # Cập nhật trạng thái hoàn thành habit ở phía cục bộ
            for h in self.data_store.habits:
                if h.id == habit_id:
                    h.completed = True

            # Đồng bộ Coin
            if "total_coins" in res:
                self.data_store.user_coins = res["total_coins"]

            # Đồng bộ EXP & Level của Pet
            if self.data_store.pet:
                if "pet_exp" in res:
                    self.data_store.pet.exp = res["pet_exp"]
                if "pet_level" in res:
                    self.data_store.pet.level = res["pet_level"]
            elif "pet_exp" in res or "pet_level" in res:
                # Thiếu snapshot pet cục bộ; tải lại từ backend.
                self._fetch_pet_data()

            # Áp dụng cả snapshot đầy đủ để phản ánh ngay mức giảm Happiness/Health
            # hằng ngày đã diễn ra cùng lần hoàn thành này.
            self._apply_pet_snapshot(res.get("pet"))

            leveled_up = res.get("leveled_up", False)
            coins_earned = res.get("coins_earned", 10)
            exp_earned = res.get("exp_earned", 20)

            msg = f"Completed habit! (+{coins_earned} Coins, +{exp_earned} EXP)"
            if leveled_up and self.data_store.pet:
                msg += f" Level up! {self.data_store.pet.pet_name} is now Level {self.data_store.pet.level}."

            return True, msg
        except APIError as e:
            if e.status_code == 401:
                self.handle_logout()
            elif e.status_code == 409:
                # Hôm nay đã hoàn thành: tải lại trạng thái chính thức để
                # UI hiển thị đúng thay vì tự suy đoán cục bộ.
                self._fetch_habits_data()
                self._fetch_pet_data()
                self._fetch_wallet()
            return False, e.message
        except Exception as e:
            return False, f"Habit completion error: {str(e)}"

    def handle_buy_item(self, item_id: int) -> Tuple[bool, str]:
        """
        Hành động mua item trong Shop -> POST /store/buy/{item_id} (mô phỏng cục bộ khi offline).
        Coin và inventory được thay bằng dữ liệu backend trả về.
        """
        if self.is_offline_guest:
            return self.data_store.buy_item(item_id)

        try:
            res = self.api.buy_item(item_id)

            if "coins" in res:
                self.data_store.user_coins = res["coins"]
            if "inventory" in res:
                self._apply_inventory(res["inventory"])

            item = res.get("item") or {}
            quantity = res.get("quantity", 0)
            return True, f"Purchased {item.get('name', 'item')}! (x{quantity} in Backpack)"
        except APIError as e:
            if e.status_code == 401:
                self.handle_logout()
            return False, e.message
        except Exception as e:
            return False, f"Purchase error: {str(e)}"

    def handle_use_item(self, item_id: int) -> Tuple[bool, str]:
        """
        Hành động sử dụng item trong Backpack -> POST /inventory/{item_id}/use
        (mô phỏng cục bộ khi offline). Chỉ số Pet và inventory lấy từ backend.
        """
        if self.is_offline_guest:
            return self.data_store.use_item(item_id)

        try:
            res = self.api.use_item(item_id)

            if "coins" in res:
                self.data_store.user_coins = res["coins"]
            if "inventory" in res:
                self._apply_inventory(res["inventory"])
            self._apply_pet_snapshot(res.get("pet"))

            item = res.get("item") or {}
            applied = res.get("applied_effects") or []
            if applied:
                summary = ", ".join(
                    f"+{effect.get('value', 0)} "
                    f"{str(effect.get('type', '')).capitalize()}"
                    for effect in applied
                )
                return True, f"Used {item.get('name', 'item')}! ({summary})"
            return True, f"Used {item.get('name', 'item')}!"
        except APIError as e:
            if e.status_code == 401:
                self.handle_logout()
            return False, e.message
        except Exception as e:
            return False, f"Item usage error: {str(e)}"

    # -------------------------------------------------------------
    # Vòng lặp sự kiện chính & render
    # -------------------------------------------------------------
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return

            if self.active_screen_name == "login":
                self.screens["login"].handle_event(event)
            else:
                current_screen = self.screens.get(self.active_screen_name)
                modal_open = bool(
                    current_screen
                    and getattr(current_screen, "is_modal_open", lambda: False)()
                )

                # Khi dialog xác nhận đang mở, chặn các nút điều hướng và
                # đăng xuất để dialog thực sự là modal.
                if not modal_open:
                    for btn in self.nav_buttons.values():
                        btn.handle_event(event)

                    self.btn_logout.handle_event(event)

                # Tab điều hướng có thể vừa đổi màn hình; lấy lại màn hình hiện tại.
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
        """Render thanh điều hướng phía trên và các chỉ báo trạng thái."""
        header_rect = pygame.Rect(0, 0, WINDOW_WIDTH, 72)
        pygame.draw.rect(self.screen, COLOR_NAV_BG, header_rect)
        pygame.draw.line(self.screen, COLOR_CARD_BORDER, (0, 72), (WINDOW_WIDTH, 72), 1)

        # Logo thương hiệu / tiêu đề ứng dụng
        draw_text(self.screen, "LittleLife", (24, 23), font_size=23, color=COLOR_PRIMARY, bold=True)

        # Các tab điều hướng
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

        # Chỉ báo hồ sơ người dùng & nút đăng xuất
        if self.current_user:
            uname = self.current_user.get("username", "User")
            # Render tên người dùng căn giữa ngay trên nút Log Out với khoảng cách gọn gàng
            draw_text(self.screen, f"👤 {uname}", (self.btn_logout.rect.centerx, 8), font_size=11, color=COLOR_TEXT_DARK, bold=True, align="center")
            self.btn_logout.render(self.screen)

        # Widget hiển thị Coin
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
                self.screens["shop"].render(
                    self.screen,
                    self.data_store.shop_catalog,
                    self.data_store.user_coins,
                    self.data_store.inventory
                )
            elif self.active_screen_name == "inventory":
                self.screens["inventory"].render(
                    self.screen,
                    self.data_store.inventory,
                    self.data_store.pet
                )

        if self.active_screen_name == "login":
            # Giữ toast của phiên bên dưới card đăng nhập để không che tiêu đề của card.
            self.notification.render(
                self.screen,
                center_x=WINDOW_WIDTH // 2,
                top_y=WINDOW_HEIGHT - 46
            )
        else:
            self.notification.render(self.screen, center_x=WINDOW_WIDTH // 2, top_y=84)
        pygame.display.flip()

    def run(self):
        """Chạy vòng lặp game chính."""
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self.handle_events()
            self.update(dt)
            self.render()

        pygame.quit()
        sys.exit()


def main():
    """Điểm khởi chạy ứng dụng."""
    app = LittleLifeApp()
    app.run()


if __name__ == "__main__":
    main()
