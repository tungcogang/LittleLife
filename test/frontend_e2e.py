"""
Kiểm thử tích hợp frontend LittleLife (Pygame headless).

Chạy controller ``LittleLifeApp`` thật với SDL dummy video driver,
gọi đúng các callback mà các nút dùng, nói chuyện với backend FastAPI thật ở
chế độ Online, và lưu ảnh chụp màn hình để kiểm tra bằng mắt.

    # terminal 1: backend phải đang chạy
    .\\.venv\\Scripts\\python.exe -B -m uvicorn backend.main:app --port 8000

    # terminal 2
    .\\.venv\\Scripts\\python.exe -B test\\frontend_e2e.py

Ảnh chụp mặc định được ghi vào ``%TEMP%/littlelife_screenshots``. Đặt
``LITTLELIFE_SCREENSHOT_DIR`` để ghi sang chỗ khác.
"""

import os
import sys
import tempfile
import time
from datetime import date, timedelta
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TESTS_DIR = Path(__file__).resolve().parent
for entry in (str(PROJECT_ROOT), str(TESTS_DIR)):
    if entry not in sys.path:
        sys.path.insert(0, entry)

import pygame  # noqa: E402

from frontend.pygame_ui.app import LittleLifeApp  # noqa: E402
from frontend.pygame_ui.api_client import APIError  # noqa: E402
from frontend.pygame_ui.text_input import TextInput  # noqa: E402
from e2e_integration import (  # noqa: E402
    api,
    cleanup_test_users,
    db_get_pet,
    db_set_pet,
    db_snapshot,
    login,
)

SCREENSHOTS = Path(
    os.environ.get(
        "LITTLELIFE_SCREENSHOT_DIR",
        str(Path(tempfile.gettempdir()) / "littlelife_screenshots"),
    )
)
CHECKED = 0


def check(condition, label, extra=""):
    global CHECKED
    CHECKED += 1
    if not condition:
        raise AssertionError(f"FAILED: {label}{(' -> ' + str(extra)) if extra else ''}")
    print(f"  PASS  {label}")


def shot(app, name):
    """Render màn hình đang hiển thị và lưu một ảnh chụp."""
    app.render()
    path = SCREENSHOTS / f"{name}.png"
    pygame.image.save(app.screen, str(path))
    check(path.exists() and path.stat().st_size > 2000, f"screenshot {name}", path)


def click_button(screen, button):
    """Gửi một click trái vào tâm nút để kiểm tra luồng UI thật."""
    event = pygame.event.Event(
        pygame.MOUSEBUTTONDOWN,
        {"button": 1, "pos": button.rect.center}
    )
    screen.handle_event(event)


def post_event(app, event):
    """Đưa sự kiện vào hàng đợi Pygame rồi để app xử lý như người dùng thật."""
    pygame.event.post(event)
    app.handle_events()


def post_click(app, pos):
    post_event(
        app,
        pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": pos})
    )


def post_text(app, text):
    post_event(app, pygame.event.Event(pygame.TEXTINPUT, {"text": text}))


def post_key(app, key, unicode=""):
    post_event(
        app,
        pygame.event.Event(
            pygame.KEYDOWN,
            {"key": key, "unicode": unicode, "mod": 0}
        )
    )


def find_catalog_item(app, name):
    for item in app.data_store.shop_catalog:
        if item.name == name:
            return item
    raise AssertionError(f"Item {name!r} missing from frontend catalog")


def run_text_input_tests():
    print("\n[0] Shared TextInput / Vietnamese (VNI)")
    field = TextInput((20, 20, 260, 40), max_length=60)
    field.is_focused = True

    def feed_text(text):
        field.handle_event(
            pygame.event.Event(pygame.TEXTINPUT, {"text": text})
        )

    feed_text("tung")
    check(field.text == "tung", "English input via TEXTINPUT")

    feed_text("Tôi uống nước")
    check(field.text == "tungTôi uống nước", "Vietnamese input via TEXTINPUT")
    feed_text(" 2L")
    check(field.text.endswith(" 2L"), "spaces and numbers are preserved")

    before = field.text
    field.handle_event(
        pygame.event.Event(
            pygame.KEYDOWN,
            {"key": pygame.K_a, "unicode": "a", "mod": 0}
        )
    )
    check(field.text == before, "printable KEYDOWN is ignored to avoid duplication")

    feed_text("a")
    check(field.text == before + "a", "one TEXTINPUT inserts exactly one character")

    field.handle_event(
        pygame.event.Event(
            pygame.KEYDOWN,
            {"key": pygame.K_BACKSPACE, "unicode": "", "mod": 0}
        )
    )
    check(field.text == before, "Backspace removes the last character")

    field.handle_event(
        pygame.event.Event(
            pygame.KEYDOWN,
            {"key": pygame.K_DELETE, "unicode": "", "mod": 0}
        )
    )
    check(field.text == before[:-1], "Delete removes the last character")

    field.clear()
    field.is_focused = True
    field.handle_event(
        pygame.event.Event(
            pygame.TEXTEDITING,
            {"text": "nước", "start": 0, "length": 0}
        )
    )
    check(
        field.composition == "nước" and field.text == "",
        "TEXTEDITING is preview-only",
    )
    surface = pygame.Surface((300, 60))
    field.render(surface)
    feed_text("nước")
    check(
        field.text == "nước" and field.composition == "",
        "TEXTINPUT commits the composition",
    )

    field.is_focused = False
    feed_text("x")
    check(field.text == "nước", "unfocused input ignores TEXTINPUT")

    field.handle_event(
        pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            {"button": 1, "pos": field.rect.center}
        )
    )
    check(field.is_focused, "click gives focus to the field")

    short = TextInput((20, 80, 220, 40), max_length=5)
    short.is_focused = True
    short.handle_event(
        pygame.event.Event(pygame.TEXTINPUT, {"text": "Uống nước"})
    )
    check(
        short.text == "Uống " and len(short.text) == 5,
        "multi-character input truncates at max_length",
        short.text,
    )

    field.clear()
    field.is_focused = True
    enter_event = pygame.event.Event(
        pygame.KEYDOWN, {"key": pygame.K_RETURN, "unicode": "", "mod": 0}
    )
    check(field.handle_event(enter_event) is True, "Enter returns True for the parent screen")
    field.composition = "nư"
    check(
        field.handle_event(enter_event) is False,
        "Enter is ignored while IME composition is active",
    )
    field.composition = ""

    field.clear()
    feed_text("Habit VNI 2L nước")
    check(
        field.text == "Habit VNI 2L nước",
        "mixed Vietnamese / English / numbers / spaces",
    )
    field.is_focused = False


def run_register_input_test(app):
    print("\n[0.1] Register screen Vietnamese input")
    login_screen = app.screens["login"]
    app.active_screen_name = "login"
    login_screen.reset_form()
    login_screen._toggle_mode()  # chuyển sang form Register

    post_click(app, login_screen.input_username.rect.center)
    post_text(app, "Người Chơi")

    # Hai sự kiện liên tiếp trong cùng batch để kiểm tra thứ tự/không mất chữ.
    for part in (" - ", "VNI"):
        pygame.event.post(pygame.event.Event(pygame.TEXTINPUT, {"text": part}))
    app.handle_events()

    check(
        login_screen.input_username.text == "Người Chơi - VNI",
        "register username accepts Vietnamese and rapid input",
        login_screen.input_username.text,
    )

    post_click(app, login_screen.input_email.rect.center)
    post_text(app, "nguoi@vidu.vn")
    check(
        login_screen.input_email.text == "nguoi@vidu.vn",
        "register email accepts text after focus switch",
    )

    post_click(app, login_screen.input_password.rect.center)
    post_text(app, "MậtKhẩu123")
    check(
        login_screen.input_password.text == "MậtKhẩu123",
        "register password accepts Vietnamese",
    )
    check(
        login_screen.input_username.text == "Người Chơi - VNI"
        and login_screen.input_email.text == "nguoi@vidu.vn",
        "focus switching keeps other fields intact",
    )

    post_key(app, pygame.K_BACKSPACE)
    check(
        login_screen.input_password.text == "MậtKhẩu12",
        "register Backspace removes one character",
    )
    post_text(app, "3")
    check(
        login_screen.input_password.text == "MậtKhẩu123",
        "typing after Backspace continues correctly",
    )

    shot(app, "06b_register_vietnamese")

    # Validation hiện có vẫn phải giữ nguyên, không bị ảnh hưởng bởi IME.
    login_screen.input_username.text = "ab"
    login_screen.input_email.text = "a@b.co"
    login_screen.input_password.text = "MậtKhẩu123"
    login_screen._submit_register()
    check(
        "at least 3" in (login_screen.error_message or ""),
        "register validation unchanged",
        login_screen.error_message,
    )

    login_screen.reset_form()


def run_offline(app):
    print("\n[1] Offline / Demo Mode")
    app.handle_continue_offline()
    check(app.is_offline_guest, "demo mode active")
    check(app.data_store.pet is not None, "demo pet available")
    app.active_screen_name = "pet"
    shot(app, "01_offline_pet")

    pet = app.data_store.pet
    check(app.data_store.user_coins == 150, "demo wallet starts at 150 coins")

    success, message = app.handle_feed_pet()
    check(success and pet.hunger == 90, "offline feed adds 15 Hunger", message)

    success, message = app.handle_play_pet()
    check(
        success and pet.hunger == 80 and pet.energy == 50 and pet.happiness == 95,
        "offline play applies -10 Hunger, -10 Energy, +15 Happiness",
        (pet.hunger, pet.energy, pet.happiness),
    )

    success, message = app.handle_sleep_pet()
    check(
        success and pet.energy == 80 and pet.health == 100,
        "offline sleep applies +30 Energy and +5 Health",
        (pet.energy, pet.health),
    )

    app.set_screen("shop")
    check(len(app.data_store.shop_catalog) == 6, "demo store exposes 6 items")
    pillow = find_catalog_item(app, "Cozy Pillow")
    tonic = find_catalog_item(app, "Herbal Tonic")

    coins_before = app.data_store.user_coins
    app.screens["shop"]._trigger_buy(pillow.id)
    check(app.data_store.user_coins == coins_before - 40, "offline pillow purchase deducts 40 coins")
    check(app.data_store.inventory[pillow.id].quantity == 1, "offline pillow added to backpack")
    shot(app, "02_offline_shop")

    app.set_screen("inventory")
    shot(app, "03_offline_inventory")
    app.screens["inventory"]._trigger_use(pillow.id)
    check(
        pet.energy == 100 and pet.health == 100 and pillow.id not in app.data_store.inventory,
        "offline pillow restores Energy first and is consumed",
        (pet.energy, pet.health),
    )

    # Mua chiếc gối thứ hai và kiểm tra cả hai hiệu ứng khi cả hai chỉ số còn chỗ.
    app.set_screen("shop")
    app.screens["shop"]._trigger_buy(pillow.id)
    pet.energy = 50
    pet.health = 50
    app.set_screen("inventory")
    app.screens["inventory"]._trigger_use(pillow.id)
    check(
        pet.energy == 70 and pet.health == 60 and pillow.id not in app.data_store.inventory,
        "offline multi-effect pillow applies +20 Energy and +10 Health",
        (pet.energy, pet.health),
    )

    # UX khi chỉ số đầy: mua tonic, làm đầy Health, rồi kiểm tra trạng thái vô hiệu hóa.
    app.set_screen("shop")
    app.screens["shop"]._trigger_buy(tonic.id)
    pet.health = 100
    app.set_screen("inventory")
    app.render()
    tonic_button = app.screens["inventory"].use_buttons[tonic.id]
    check(
        not tonic_button.enabled and tonic_button.text == "Full",
        "backpack disables an item when all its stats are full",
        tonic_button.text,
    )
    app.screens["inventory"]._trigger_use(tonic.id)
    check(app.data_store.inventory[tonic.id].quantity == 1, "offline full-stat use consumes nothing")

    app.set_screen("habit")
    habits_before = len(app.data_store.habits)
    success, message = app.handle_create_habit("Offline Stretch", "Stretch for five minutes")
    check(success and len(app.data_store.habits) == habits_before + 1, "offline habit creation", message)
    new_habit = app.data_store.habits[-1]
    coins_before = app.data_store.user_coins
    success, message = app.handle_complete_habit(new_habit.id)
    check(success and app.data_store.user_coins == coins_before + 10, "offline habit completion rewards coins", message)
    success, message = app.handle_complete_habit(new_habit.id)
    check(not success and "already completed" in message, "offline duplicate completion blocked", message)
    shot(app, "04_offline_habits")

    # --- Xóa habit qua dialog xác nhận (Demo Mode) ---
    app.set_screen("habit")
    habit_screen = app.screens["habit"]
    app.render()
    habit_screen.scroll_offset = habit_screen._max_scroll
    app.render()

    coins_before_delete = app.data_store.user_coins
    habits_before_delete = len(app.data_store.habits)

    delete_button = habit_screen.delete_buttons[new_habit.id]
    click_button(habit_screen, delete_button)
    check(habit_screen.pending_delete_id == new_habit.id, "delete click opens confirmation dialog")
    shot(app, "04b_offline_delete_dialog")

    # Dialog phải chặn nút Complete phía sau.
    blocked_habit = next(
        habit for habit in app.data_store.habits
        if not habit.completed and habit.id in habit_screen.habit_buttons
    )
    click_button(habit_screen, habit_screen.habit_buttons[blocked_habit.id])
    check(not blocked_habit.completed, "confirmation dialog blocks the Complete button")

    click_button(habit_screen, habit_screen.dialog_cancel)
    check(habit_screen.pending_delete_id is None, "Cancel closes the dialog")
    check(len(app.data_store.habits) == habits_before_delete, "Cancel keeps the habit")
    check(app.data_store.user_coins == coins_before_delete, "Cancel keeps the wallet unchanged")

    app.render()
    habit_screen.scroll_offset = habit_screen._max_scroll
    app.render()
    delete_button = habit_screen.delete_buttons[new_habit.id]
    click_button(habit_screen, delete_button)
    click_button(habit_screen, habit_screen.dialog_delete)
    app.render()

    check(
        len(app.data_store.habits) == habits_before_delete - 1,
        "confirmed deletion removes exactly one habit",
    )
    check(
        all(habit.id != new_habit.id for habit in app.data_store.habits),
        "deleted demo habit is gone",
    )
    check(
        app.data_store.user_coins == coins_before_delete,
        "demo deletion does not refund coins",
    )
    check(
        any(habit.id == blocked_habit.id for habit in app.data_store.habits),
        "other demo habits remain after deletion",
    )
    shot(app, "04c_offline_habits_after_delete")

    # Nút Complete vẫn hoạt động sau khi thêm nút xóa.
    app.render()
    blocked_button = habit_screen.habit_buttons.get(blocked_habit.id)
    check(blocked_button is not None, "remaining habit still has a Complete button")
    coins_before_complete = app.data_store.user_coins
    click_button(habit_screen, blocked_button)
    check(
        blocked_habit.completed
        and app.data_store.user_coins == coins_before_complete + 10,
        "Complete still works after deletion controls",
    )

    app.handle_logout()
    check(app.active_screen_name == "login", "offline logout returns to login")
    check(app.data_store.user_coins == 150, "logout resets demo state", app.data_store.user_coins)


def run_online(app, username, password, email_domain):
    print("\n[2] Login screen and registration")
    app.active_screen_name = "login"
    shot(app, "05_login_signin")
    login_screen = app.screens["login"]
    login_screen._toggle_mode()
    shot(app, "06_login_register")
    run_register_input_test(app)

    success, message = app.handle_register_submit(username, f"{username}@{email_domain}", password)
    check(success and not app.is_offline_guest, "registration signs the player in", message)
    check(app.active_screen_name == "pet", "registration lands on the pet screen", app.active_screen_name)
    check(app.data_store.pet is None, "new account shows the adoption screen")
    shot(app, "07_online_adopt_pet")

    success, message = app.handle_create_pet("UiPal")
    check(success and app.data_store.pet is not None, "adopt pet through the UI controller", message)
    pet = app.data_store.pet
    check(
        (pet.hunger, pet.happiness, pet.energy, pet.health) == (75, 80, 60, 95),
        "adopted pet vitals loaded from backend",
        (pet.hunger, pet.happiness, pet.energy, pet.health),
    )
    shot(app, "08_online_pet")

    print("\n[3] Habits through the Habit screen")
    app.set_screen("habit")
    habit_screen = app.screens["habit"]
    vietnamese_habit_title = "Uống 2L nước mỗi sáng"

    post_click(app, habit_screen.input_title.rect.center)
    post_text(app, vietnamese_habit_title)
    post_click(app, habit_screen.input_description.rect.center)
    post_text(app, "Nhắc nhở bản thân")
    post_key(app, pygame.K_RETURN)
    app.render()  # xóa cờ chặn đang xử lý

    check(
        any(habit.title == vietnamese_habit_title for habit in app.data_store.habits),
        "Vietnamese habit created from the on-screen form",
        [habit.title for habit in app.data_store.habits],
    )

    for index in range(2, 7):
        success, message = app.handle_create_habit(f"UI Habit {index}", "Created by frontend test")
        check(success, f"create habit {index}", message)

    habit_screen.scroll_offset = 0
    shot(app, "09_online_habits")

    check(len(app.data_store.habits) == 6, "six habits visible to the UI", len(app.data_store.habits))
    check(pet.level == 1 and pet.exp == 0, "pet starts at level 1 / 0 EXP")

    for habit in list(app.data_store.habits):
        success, message = app.handle_complete_habit(habit.id)
        check(success, f"complete habit {habit.id}", message)

    check(app.data_store.user_coins == 60, "habit rewards synced to the wallet", app.data_store.user_coins)
    check(pet.level == 2 and pet.exp == 20, "pet level-up synced from backend", (pet.level, pet.exp))
    check(all(habit.completed for habit in app.data_store.habits), "completed flags synced to the UI")
    shot(app, "10_online_habits_completed")

    habit_screen.scroll_offset = 120
    shot(app, "11_online_habits_scrolled")
    habit_screen.scroll_offset = 0

    print("\n[4] Store affordability and Backpack")
    app.set_screen("shop")
    app.render()
    check(len(app.data_store.shop_catalog) == 6, "store catalog loaded from backend", len(app.data_store.shop_catalog))
    shop_screen = app.screens["shop"]
    enabled_at_60 = [
        item.name for item in app.data_store.shop_catalog
        if shop_screen.buy_buttons[item.id].enabled
    ]
    check(len(enabled_at_60) == 6, "all 6 items are affordable at 60 coins", enabled_at_60)

    pillow = find_catalog_item(app, "Cozy Pillow")
    biscuit = find_catalog_item(app, "Crispy Biscuit")

    success, message = app.handle_buy_item(pillow.id)
    check(success and app.data_store.user_coins == 20, "Cozy Pillow purchase deducts 40 coins", message)
    check(app.data_store.inventory[pillow.id].quantity == 1, "Cozy Pillow appears in the backpack")

    # Store cố ý vẫn hiển thị mọi vật phẩm; chỉ khả năng mua
    # thay đổi. Kiểm tra hành vi được giữ nguyên đó thay vì lọc danh sách.
    app.set_screen("shop")
    app.render()
    enabled_at_20 = [
        item.name for item in app.data_store.shop_catalog
        if shop_screen.buy_buttons[item.id].enabled
    ]
    check(enabled_at_20 == ["Crispy Biscuit"], "at 20 coins only the 15-coin item is buyable", enabled_at_20)
    check(len(shop_screen.buy_buttons) == 6, "unaffordable items remain visible in the Store", len(shop_screen.buy_buttons))
    shot(app, "12_online_shop")

    success, message = app.handle_buy_item(biscuit.id)
    check(success and app.data_store.user_coins == 5, "second purchase deducts 15 coins", message)
    app.set_screen("shop")
    app.render()
    check(
        not any(button.enabled for button in shop_screen.buy_buttons.values()),
        "no Buy button is enabled at 5 coins",
    )

    app.set_screen("inventory")
    shot(app, "13_online_inventory")

    success, message = app.handle_use_item(pillow.id)
    check(
        success and pet.energy == 80 and pet.health == 100,
        "using the pillow updates both pet stats in the UI",
        (message, pet.energy, pet.health),
    )
    check("Energy" in message and "Health" in message, "usage message lists both effects", message)
    check(pillow.id not in app.data_store.inventory, "used-up pillow leaves the backpack")

    success, message = app.handle_use_item(biscuit.id)
    check(success and pet.hunger == 100, "using the biscuit fills hunger in the UI", (message, pet.hunger))
    check(biscuit.id not in app.data_store.inventory, "used-up biscuit leaves the backpack")

    print("\n[5] Care and daily decay")
    success, message = app.handle_play_pet()
    check(
        success and pet.hunger == 90 and pet.energy == 70 and pet.happiness == 95,
        "UI play applies the new Hunger/Energy/Happiness values",
        (message, pet.hunger, pet.energy, pet.happiness),
    )

    success, message = app.handle_sleep_pet()
    check(
        success and pet.energy == 100 and pet.health == 100,
        "UI sleep restores Energy and Health",
        (message, pet.energy, pet.health),
    )

    success, message = app.handle_feed_pet()
    check(success and pet.hunger == 100, "UI feed adds 15 Hunger and clamps at 100", message)

    yesterday = date.today() - timedelta(days=1)
    db_set_pet(username, last_decay_date=yesterday)
    app._fetch_pet_data()
    pet = app.data_store.pet
    check(
        pet.happiness == 85 and pet.health == 95,
        "screen refresh applies one day of decay through the API",
        (pet.happiness, pet.health),
    )
    app._fetch_pet_data()
    pet = app.data_store.pet
    check(
        pet.happiness == 85 and pet.health == 95,
        "another refresh on the same day does not decay again",
        (pet.happiness, pet.health),
    )
    db_pet = db_get_pet(username)
    check(db_pet["last_decay_date"] == date.today(), "decay date persisted in the database", db_pet)

    app.set_screen("pet")
    shot(app, "14_online_pet_decay")

    print("\n[6] Persistence across logout/login")
    app.handle_logout()
    check(
        app.active_screen_name == "login"
        and app.current_user is None
        and not app.is_offline_guest,
        "logout clears the online session",
    )

    success, message = app.handle_login_submit(username, password)
    check(success, "re-login through the UI controller", message)
    check(app.data_store.user_coins == 5, "coins restored after re-login", app.data_store.user_coins)
    check(app.data_store.pet.level == 2 and app.data_store.pet.exp == 20, "pet progression restored")
    check(
        (app.data_store.pet.hunger, app.data_store.pet.happiness,
         app.data_store.pet.energy, app.data_store.pet.health) == (100, 85, 100, 95),
        "pet vitals and decay restored",
        (app.data_store.pet.hunger, app.data_store.pet.happiness,
         app.data_store.pet.energy, app.data_store.pet.health),
    )
    check(app.data_store.inventory == {}, "used-up items remain gone after re-login")
    check(
        len(app.data_store.habits) == 6 and all(h.completed for h in app.data_store.habits),
        "habit state restored",
    )
    check(
        any(h.title == vietnamese_habit_title for h in app.data_store.habits),
        "Vietnamese habit name persisted after re-login",
        [h.title for h in app.data_store.habits],
    )

    print("\n[7] Delete Habit")
    app.set_screen("habit")
    habit_screen = app.screens["habit"]

    success, message = app.handle_create_habit("Temp Delete", "Created for delete test")
    check(success, "create temp habit for deletion", message)
    temp_habit = next(h for h in app.data_store.habits if h.title == "Temp Delete")

    success, message = app.handle_complete_habit(temp_habit.id)
    check(success, "complete temp habit before deletion", message)
    coins_after_reward = app.data_store.user_coins
    exp_after_reward = app.data_store.pet.exp
    check(
        coins_after_reward == 15 and exp_after_reward == 40,
        "temp habit rewards applied",
        (coins_after_reward, exp_after_reward),
    )

    app.render()
    habit_screen.scroll_offset = habit_screen._max_scroll
    app.render()
    delete_button = habit_screen.delete_buttons[temp_habit.id]
    click_button(habit_screen, delete_button)
    check(habit_screen.pending_delete_id == temp_habit.id, "online delete opens confirmation dialog")
    shot(app, "15_online_delete_dialog")

    click_button(habit_screen, habit_screen.dialog_cancel)
    check(habit_screen.pending_delete_id is None, "online Cancel closes the dialog")
    check(
        any(h.id == temp_habit.id for h in app.data_store.habits),
        "online Cancel keeps the habit",
    )

    app.render()
    habit_screen.scroll_offset = habit_screen._max_scroll
    app.render()
    delete_button = habit_screen.delete_buttons[temp_habit.id]
    click_button(habit_screen, delete_button)

    original_delete = app.api.delete_habit

    def failing_delete(habit_id):
        raise APIError(0, "Backend unavailable for test")

    app.api.delete_habit = failing_delete
    click_button(habit_screen, habit_screen.dialog_delete)
    app.render()

    check(
        any(h.id == temp_habit.id for h in app.data_store.habits),
        "failed backend deletion keeps the habit on screen",
    )
    check(
        app.data_store.user_coins == coins_after_reward
        and app.data_store.pet.exp == exp_after_reward,
        "failed deletion keeps rewards unchanged",
    )

    app.api.delete_habit = original_delete

    app.render()
    habit_screen.scroll_offset = habit_screen._max_scroll
    app.render()
    delete_button = habit_screen.delete_buttons[temp_habit.id]
    click_button(habit_screen, delete_button)

    delete_calls = []
    original_success_delete = app.api.delete_habit

    def counting_delete(habit_id):
        delete_calls.append(habit_id)
        return original_success_delete(habit_id)

    app.api.delete_habit = counting_delete
    click_button(habit_screen, habit_screen.dialog_delete)
    click_button(habit_screen, habit_screen.dialog_delete)
    app.api.delete_habit = original_success_delete
    check(len(delete_calls) == 1, "double-click sends only one delete request", delete_calls)
    app.render()

    check(
        all(h.id != temp_habit.id for h in app.data_store.habits),
        "confirmed online deletion removes the habit",
    )
    check(
        len(app.data_store.habits) == 6,
        "online habit list returns to 6 habits",
        len(app.data_store.habits),
    )
    check(
        app.data_store.user_coins == coins_after_reward
        and app.data_store.pet.exp == exp_after_reward,
        "online deletion does not refund Coins or EXP",
    )

    # Danh sách vẫn cuộn được sau khi thêm nút xóa và xóa habit.
    original_get_pos = pygame.mouse.get_pos
    pygame.mouse.get_pos = lambda: (300, 300)
    habit_screen.scroll_offset = 0
    habit_screen.handle_event(pygame.event.Event(pygame.MOUSEWHEEL, {"y": -1}))
    pygame.mouse.get_pos = original_get_pos
    check(
        habit_screen.scroll_offset > 0,
        "habit list still scrolls after deletion",
        habit_screen.scroll_offset,
    )
    habit_screen.scroll_offset = 0
    app.render()

    token = login(username, password)
    status, habits = api("GET", "/habits/", token=token)
    check(
        status == 200 and len(habits) == 6
        and all(h["id"] != temp_habit.id for h in habits),
        "backend confirms the habit was deleted",
        habits,
    )
    check(
        any(h["title"] == vietnamese_habit_title for h in habits),
        "Vietnamese habit name returned by backend",
        [h["title"] for h in habits],
    )
    status, me = api("GET", "/auth/me", token=token)
    check(me["coins"] == 15, "backend wallet unchanged by deletion", me)
    status, backend_pet = api("GET", "/pets/me", token=token)
    check(
        backend_pet["exp"] == 40 and backend_pet["level"] == 2,
        "backend pet progression unchanged by deletion",
        backend_pet,
    )

    print("\n[8] Stability & error handling")
    for _ in range(3):
        for screen_name in ("pet", "habit", "shop", "inventory"):
            app.set_screen(screen_name)
            app.render()
    check(True, "repeated screen switching does not crash")

    original_base_url = app.api.base_url
    app.api.base_url = "http://127.0.0.1:1"
    success, message = app.handle_login_submit("nobody", "Password123")
    app.api.base_url = original_base_url
    check(
        not success and "Cannot connect" in message,
        "backend unavailable returns a clear error",
        message,
    )
    check(
        app.current_user is not None,
        "a failed login does not clear the active session",
    )


def main():
    started = time.time()
    suffix = str(int(started))
    username = f"e2e_ui_{suffix}"
    password = "UiTestPass123!"
    email_domain = "e2e.invalid"
    before = db_snapshot()

    SCREENSHOTS.mkdir(parents=True, exist_ok=True)

    app = None
    failure = None

    try:
        app = LittleLifeApp()
        check(app.active_screen_name == "login", "app starts on the login screen")

        run_text_input_tests()
        run_offline(app)
        run_online(app, username, password, email_domain)

        # Đối chiếu trạng thái UI với backend sau khi đăng nhập lại.
        token = login(username, password)
        status, inventory = api("GET", "/inventory/", token=token)
        check(status == 200 and inventory["items"] == [], "backend backpack matches the UI", inventory)
        status, me = api("GET", "/auth/me", token=token)
        check(me["coins"] == 15, "backend wallet matches the UI", me)
        status, pet = api("GET", "/pets/me", token=token)
        check(
            (pet["hunger"], pet["happiness"], pet["energy"], pet["health"]) == (100, 85, 100, 95),
            "backend pet vitals match the UI",
            pet,
        )
        check(pet["last_decay_date"] == date.today().isoformat(), "backend decay date matches", pet)
    except Exception as error:  # noqa: BLE001 - reported after cleanup
        import traceback
        traceback.print_exc()
        failure = error
    finally:
        if app is not None:
            app.handle_logout()
            pygame.quit()
        removed = cleanup_test_users()
        print(f"\n  INFO  temporary accounts removed: {removed or 'none'}")

    after = db_snapshot()
    keys = ("users", "pets", "habits", "completions", "inventory", "transactions", "tung_coins", "tung_pet")
    mismatches = {key: (before[key], after[key]) for key in keys if before[key] != after[key]}
    if mismatches:
        print(f"  FAIL  existing database rows changed: {mismatches}")
        failure = failure or AssertionError(f"Existing database rows changed: {mismatches}")
    else:
        print("  PASS  existing database rows unchanged")

    if failure:
        raise failure

    print("\n" + "=" * 62)
    print(f"ALL {CHECKED} FRONTEND CHECKS PASSED in {round(time.time() - started, 2)}s")
    print(f"Screenshots: {SCREENSHOTS}")
    print("=" * 62)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:  # noqa: BLE001 - test harness reports and exits non-zero
        print("\n" + "=" * 62)
        print(f"FRONTEND TEST FAILED after {CHECKED} checks")
        print(f"{type(error).__name__}: {error}")
        print("=" * 62)
        sys.exit(1)
