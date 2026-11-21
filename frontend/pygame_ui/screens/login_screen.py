"""
Màn hình đăng nhập cho LittleLife Pygame UI.
Cung cấp màn hình xác thực dễ chịu để đăng nhập (POST /auth/login) hoặc tạo
tài khoản mới (POST /auth/register), cùng tùy chọn chế độ offline/demo.
"""
from typing import Callable, List, Optional, Tuple
import os
import pygame
try:
    from ..theme import (
        COLOR_BG,
        COLOR_PRIMARY,
        COLOR_PRIMARY_HOVER,
        COLOR_PRIMARY_DARK,
        COLOR_ACCENT,
        COLOR_TEXT_DARK,
        COLOR_TEXT_MUTED,
        COLOR_TEXT_LIGHT,
        COLOR_CARD_BG,
        COLOR_CARD_BORDER,
        COLOR_DANGER
    )
    from ..components import Card, Button, draw_text, fit_text
    from ..text_input import TextInput
except ImportError:
    from theme import (
        COLOR_BG,
        COLOR_PRIMARY,
        COLOR_PRIMARY_HOVER,
        COLOR_PRIMARY_DARK,
        COLOR_ACCENT,
        COLOR_TEXT_DARK,
        COLOR_TEXT_MUTED,
        COLOR_TEXT_LIGHT,
        COLOR_CARD_BG,
        COLOR_CARD_BORDER,
        COLOR_DANGER
    )
    from components import Card, Button, draw_text, fit_text
    from text_input import TextInput


class LoginScreen:
    """Màn hình xác thực để đăng nhập hoặc đăng ký tài khoản LittleLife."""
    def __init__(
        self,
        on_login_submit: Callable[[str, str], Tuple[bool, str]],
        on_continue_offline: Optional[Callable[[], None]] = None,
        on_register_submit: Optional[Callable[[str, str, str], Tuple[bool, str]]] = None
    ):
        self.on_login_submit = on_login_submit
        self.on_continue_offline = on_continue_offline
        self.on_register_submit = on_register_submit

        # Kích thước card căn giữa
        card_w, card_h = 420, 460
        card_x = (960 - card_w) // 2
        card_y = (640 - card_h) // 2

        self.card = Card(
            (card_x, card_y, card_w, card_h),
            title="Welcome to LittleLife",
            subtitle="Sign in to sync your pet and daily progress"
        )

        self.card_x = card_x
        self.card_y = card_y
        self.input_x = card_x + 35
        self.input_w = card_w - 70

        self.input_username = TextInput(
            rect=(self.input_x, card_y + 130, self.input_w, 42),
            placeholder="Enter username (min 3 chars)",
            max_length=50
        )
        self.input_username.is_focused = True  # Focus sẵn theo mặc định

        self.input_email = TextInput(
            rect=(self.input_x, card_y + 182, self.input_w, 38),
            placeholder="you@example.com",
            max_length=100
        )

        self.input_password = TextInput(
            rect=(self.input_x, card_y + 215, self.input_w, 42),
            placeholder="Enter password (min 8 chars)",
            is_password=True,
            max_length=128
        )

        # Các nút
        self.btn_login = Button(
            rect=(self.input_x, card_y + 295, self.input_w, 44),
            text="Sign In",
            on_click=self._submit,
            bg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            font_size=15
        )

        self.btn_register = Button(
            rect=(self.input_x, card_y + 288, self.input_w, 42),
            text="Create Account",
            on_click=self._submit,
            bg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            font_size=15
        )

        self.btn_guest = Button(
            rect=(self.input_x, card_y + 355, 170, 38),
            text="Demo Mode",
            on_click=self._guest,
            bg_color=(240, 235, 225),
            hover_color=(230, 224, 212),
            text_color=COLOR_TEXT_DARK,
            font_size=12
        )

        self.btn_mode = Button(
            rect=(self.input_x + 180, card_y + 355, 170, 38),
            text="Create Account",
            on_click=self._toggle_mode,
            bg_color=(240, 235, 225),
            hover_color=(230, 224, 212),
            text_color=COLOR_TEXT_DARK,
            font_size=12
        )

        self.mode = "login"  # "login" hoặc "register"
        self.error_message: Optional[str] = None
        self.is_loading: bool = False

    # ------------------------------------------------------------------
    # Các hàm phụ cho chế độ / form
    # ------------------------------------------------------------------
    def _active_inputs(self) -> List[TextInput]:
        if self.mode == "register":
            return [self.input_username, self.input_email, self.input_password]
        return [self.input_username, self.input_password]

    def _layout(self):
        """Đặt vị trí các ô nhập và nút theo chế độ đang hoạt động."""
        if self.mode == "register":
            self.card.subtitle = "Create a new account to begin your journey"
            self.input_username.rect.topleft = (self.input_x, self.card_y + 124)
            self.input_username.rect.height = 38
            self.input_email.rect.topleft = (self.input_x, self.card_y + 182)
            self.input_password.rect.topleft = (self.input_x, self.card_y + 240)
            self.input_password.rect.height = 38
            self.btn_mode.rect = pygame.Rect(self.input_x, self.card_y + 336, self.input_w, 32)
            self.btn_mode.text = "← Back to Sign In"
        else:
            self.card.subtitle = "Sign in to sync your pet and daily progress"
            self.input_username.rect.topleft = (self.input_x, self.card_y + 130)
            self.input_username.rect.height = 42
            self.input_email.rect.topleft = (self.input_x, self.card_y + 182)
            self.input_password.rect.topleft = (self.input_x, self.card_y + 215)
            self.input_password.rect.height = 42
            self.btn_mode.rect = (
                pygame.Rect(self.input_x, self.card_y + 355, self.input_w, 38)
                if not self.on_continue_offline
                else pygame.Rect(self.input_x + 180, self.card_y + 355, 170, 38)
            )
            self.btn_mode.text = "Create Account"

    def _toggle_mode(self):
        self.mode = "register" if self.mode == "login" else "login"
        self.error_message = None
        self._layout()

        for field in (self.input_username, self.input_email, self.input_password):
            field.is_focused = False
        self.input_username.is_focused = True

    def reset_form(self):
        """Xóa thông tin đăng nhập và quay về form đăng nhập (dùng sau khi đăng nhập/đăng xuất)."""
        self.input_username.clear()
        self.input_email.clear()
        self.input_password.clear()
        self.error_message = None
        self.is_loading = False
        self.mode = "login"
        self._layout()
        self.input_username.is_focused = True
        self.input_password.is_focused = False
        self.input_email.is_focused = False

    # ------------------------------------------------------------------
    # Các hành động
    # ------------------------------------------------------------------
    def _submit(self):
        if self.mode == "register":
            self._submit_register()
        else:
            self._submit_login()

    def _submit_login(self):
        username = self.input_username.text.strip()
        password = self.input_password.text.strip()

        if not username:
            self.error_message = "Please enter your username."
            return
        if not password:
            self.error_message = "Please enter your password."
            return

        self.error_message = None
        self.is_loading = True
        success, msg = self.on_login_submit(username, password)
        self.is_loading = False

        if not success:
            self.error_message = msg

    def _submit_register(self):
        username = self.input_username.text.strip()
        email = self.input_email.text.strip()
        password = self.input_password.text.strip()

        if len(username) < 3:
            self.error_message = "Username must be at least 3 characters."
            return
        if "@" not in email or "." not in email or len(email) < 5:
            self.error_message = "Please enter a valid email address."
            return
        if len(password) < 8:
            self.error_message = "Password must be at least 8 characters."
            return
        if not self.on_register_submit:
            self.error_message = "Registration is not available."
            return

        self.error_message = None
        self.is_loading = True
        success, msg = self.on_register_submit(username, email, password)
        self.is_loading = False

        if not success:
            self.error_message = msg

    def _guest(self):
        if self.on_continue_offline:
            self.on_continue_offline()

    # ------------------------------------------------------------------
    # Sự kiện & render
    # ------------------------------------------------------------------
    def handle_event(self, event: pygame.event.Event):
        # Phím Tab chuyển vòng qua các ô đang hiển thị.
        if event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
            inputs = self._active_inputs()
            focused_index = next((i for i, field in enumerate(inputs) if field.is_focused), None)
            for field in inputs:
                field.is_focused = False
            if focused_index is None:
                inputs[0].is_focused = True
            else:
                inputs[(focused_index + 1) % len(inputs)].is_focused = True
            return

        # Enter chuyển sang ô kế tiếp, hoặc gửi form nếu đang ở ô cuối cùng.
        inputs = self._active_inputs()
        for index, field in enumerate(inputs):
            if field.handle_event(event):
                field.is_focused = False
                if index + 1 < len(inputs):
                    inputs[index + 1].is_focused = True
                else:
                    self._submit()
                return

        if self.mode == "login":
            self.btn_login.handle_event(event)
            if self.on_continue_offline:
                self.btn_guest.handle_event(event)
        else:
            self.btn_register.handle_event(event)

        self.btn_mode.handle_event(event)

    def update(self, dt: float):
        self.input_username.update(dt)
        self.input_email.update(dt)
        self.input_password.update(dt)

    def render(self, surface: pygame.Surface):
        # Nền toàn màn hình
        surface.fill(COLOR_BG)

        # Render card đăng nhập chính
        self.card.render(surface)

        card_rect = self.card.rect

        if self.mode == "login":
            # Nhãn và ô nhập liệu
            draw_text(surface, "Username", (card_rect.x + 35, card_rect.y + 106), font_size=13, color=COLOR_TEXT_DARK, bold=True)
            self.input_username.render(surface)

            draw_text(surface, "Password", (card_rect.x + 35, card_rect.y + 191), font_size=13, color=COLOR_TEXT_DARK, bold=True)
            self.input_password.render(surface)

            # Các nút
            self.btn_login.render(surface)
            if self.on_continue_offline:
                self.btn_guest.render(surface)
            self.btn_mode.render(surface)
        else:
            draw_text(surface, "Username", (card_rect.x + 35, card_rect.y + 104), font_size=13, color=COLOR_TEXT_DARK, bold=True)
            self.input_username.render(surface)

            draw_text(surface, "Email", (card_rect.x + 35, card_rect.y + 162), font_size=13, color=COLOR_TEXT_DARK, bold=True)
            self.input_email.render(surface)

            draw_text(surface, "Password", (card_rect.x + 35, card_rect.y + 220), font_size=13, color=COLOR_TEXT_DARK, bold=True)
            self.input_password.render(surface)

            self.btn_register.render(surface)
            self.btn_mode.render(surface)

        # Gợi ý địa chỉ backend ở cuối card
        backend_url = os.getenv("LITTLELIFE_API_URL", "http://127.0.0.1:8000")
        draw_text(surface, f"Backend API: {backend_url}", (card_rect.centerx, card_rect.bottom - 22), font_size=11, color=COLOR_TEXT_MUTED, align="center")

        # Banner thông báo lỗi nếu đăng nhập/đăng ký thất bại
        if self.error_message:
            err_rect = pygame.Rect(card_rect.x + 35, card_rect.y + 70, card_rect.width - 70, 30)
            pygame.draw.rect(surface, (254, 226, 226), err_rect, border_radius=6)
            pygame.draw.rect(surface, (239, 68, 68), err_rect, width=1, border_radius=6)
            err_txt = fit_text(self.error_message, 12, err_rect.width - 20)
            draw_text(surface, f"⚠ {err_txt}", err_rect.center, font_size=12, color=COLOR_DANGER, bold=True, align="center")

        # Gợi ý đăng ký
        if self.mode == "login":
            draw_text(surface, "New player? Use \"Create Account\" to register.", (card_rect.centerx, card_rect.y + 405), font_size=11, color=COLOR_TEXT_MUTED, align="center")
        else:
            draw_text(surface, "Password must be at least 8 characters.", (card_rect.centerx, card_rect.y + 378), font_size=11, color=COLOR_TEXT_MUTED, align="center")
