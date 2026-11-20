"""
Login Screen for LittleLife Pygame UI.
Provides a cozy authentication modal/screen to connect to POST /auth/login.
Supports:
- Username & Password inputs with masking
- Direct login submission
- Clear error banner displays (invalid credentials, connection failed)
- Option to continue in offline/guest mode using local mock data
"""
from typing import Callable, Tuple, Optional
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
    from ..components import Card, Button, draw_text
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
    from components import Card, Button, draw_text
    from text_input import TextInput


class LoginScreen:
    """Authentication screen for logging into the LittleLife FastAPI backend."""
    def __init__(
        self,
        on_login_submit: Callable[[str, str], Tuple[bool, str]],
        on_continue_offline: Optional[Callable[[], None]] = None
    ):
        self.on_login_submit = on_login_submit
        self.on_continue_offline = on_continue_offline

        # Center card dimensions
        card_w, card_h = 420, 460
        card_x = (960 - card_w) // 2
        card_y = (640 - card_h) // 2

        self.card = Card(
            (card_x, card_y, card_w, card_h),
            title="Welcome to LittleLife",
            subtitle="Sign in to sync your pet and daily progress"
        )

        input_x = card_x + 35
        input_w = card_w - 70

        self.input_username = TextInput(
            rect=(input_x, card_y + 130, input_w, 42),
            placeholder="Enter username (min 3 chars)",
            max_length=50
        )
        self.input_username.is_focused = True  # Focus by default

        self.input_password = TextInput(
            rect=(input_x, card_y + 215, input_w, 42),
            placeholder="Enter password (min 8 chars)",
            is_password=True,
            max_length=128
        )

        # Buttons
        self.btn_login = Button(
            rect=(input_x, card_y + 295, input_w, 44),
            text="Sign In",
            on_click=self._submit,
            bg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            font_size=15
        )

        self.btn_guest = Button(
            rect=(input_x, card_y + 355, input_w, 38),
            text="Continue in Offline / Demo Mode",
            on_click=self._guest,
            bg_color=(240, 235, 225),
            hover_color=(230, 224, 212),
            text_color=COLOR_TEXT_DARK,
            font_size=13
        )

        self.error_message: Optional[str] = None
        self.is_loading: bool = False

    def _submit(self):
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

    def _guest(self):
        if self.on_continue_offline:
            self.on_continue_offline()

    def handle_event(self, event: pygame.event.Event):
        # Allow Tab to switch between inputs
        if event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
            if self.input_username.is_focused:
                self.input_username.is_focused = False
                self.input_password.is_focused = True
            else:
                self.input_password.is_focused = False
                self.input_username.is_focused = True
            return

        # Enter submits from either input
        if self.input_username.handle_event(event):
            self.input_username.is_focused = False
            self.input_password.is_focused = True
        elif self.input_password.handle_event(event):
            self._submit()

        self.btn_login.handle_event(event)
        self.btn_guest.handle_event(event)

    def update(self, dt: float):
        self.input_username.update(dt)
        self.input_password.update(dt)

    def render(self, surface: pygame.Surface):
        # Full screen background
        surface.fill(COLOR_BG)

        # Render Main Login Card
        self.card.render(surface)

        card_rect = self.card.rect

        # Input labels
        draw_text(surface, "Username", (card_rect.x + 35, card_rect.y + 106), font_size=13, color=COLOR_TEXT_DARK, bold=True)
        self.input_username.render(surface)

        draw_text(surface, "Password", (card_rect.x + 35, card_rect.y + 191), font_size=13, color=COLOR_TEXT_DARK, bold=True)
        self.input_password.render(surface)

        # Buttons
        self.btn_login.render(surface)
        self.btn_guest.render(surface)

        # Backend host hint at bottom of card
        draw_text(surface, "Backend API: http://127.0.0.1:8000", (card_rect.centerx, card_rect.bottom - 22), font_size=11, color=COLOR_TEXT_MUTED, align="center")

        # Error notification banner if login failed
        if self.error_message:
            err_rect = pygame.Rect(card_rect.x + 35, card_rect.y + 70, card_rect.width - 70, 30)
            pygame.draw.rect(surface, (254, 226, 226), err_rect, border_radius=6)
            pygame.draw.rect(surface, (239, 68, 68), err_rect, width=1, border_radius=6)
            # Clip error message for neat display
            err_txt = self.error_message
            if len(err_txt) > 42:
                err_txt = err_txt[:39] + "..."
            draw_text(surface, f"⚠ {err_txt}", err_rect.center, font_size=12, color=COLOR_DANGER, bold=True, align="center")
