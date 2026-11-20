"""
TextInput component for Pygame UI.
Provides a clean, cozy text field with focus state, placeholder text, and password masking.
"""
from typing import Tuple, Optional
import pygame
try:
    from .theme import (
        COLOR_CARD_BG,
        COLOR_CARD_BORDER,
        COLOR_PRIMARY,
        COLOR_TEXT_DARK,
        COLOR_TEXT_MUTED,
        get_font
    )
except ImportError:
    from theme import (
        COLOR_CARD_BG,
        COLOR_CARD_BORDER,
        COLOR_PRIMARY,
        COLOR_TEXT_DARK,
        COLOR_TEXT_MUTED,
        get_font
    )


class TextInput:
    """Cozy text input field supporting focus, placeholder, cursor, and password masking."""
    def __init__(
        self,
        rect: Tuple[int, int, int, int] | pygame.Rect,
        placeholder: str = "",
        initial_value: str = "",
        is_password: bool = False,
        max_length: int = 50,
        font_size: int = 15,
        border_radius: int = 8
    ):
        self.rect = pygame.Rect(rect)
        self.placeholder = placeholder
        self.text = initial_value
        self.is_password = is_password
        self.max_length = max_length
        self.font_size = font_size
        self.border_radius = border_radius

        self.is_focused = False
        self.cursor_timer = 0.0
        self.show_cursor = True

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle clicks for focus, and keyboard inputs. Returns True if enter was pressed."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.is_focused = self.rect.collidepoint(event.pos)
            self.cursor_timer = 0.0
            self.show_cursor = True
            return False

        if not self.is_focused:
            return False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                return True
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_ESCAPE:
                self.is_focused = False
            elif event.unicode and len(self.text) < self.max_length and event.unicode.isprintable():
                self.text += event.unicode

        return False

    def update(self, dt: float):
        if self.is_focused:
            self.cursor_timer += dt
            if self.cursor_timer >= 0.5:
                self.cursor_timer = 0.0
                self.show_cursor = not self.show_cursor
        else:
            self.show_cursor = False

    def render(self, surface: pygame.Surface):
        # Background
        pygame.draw.rect(surface, COLOR_CARD_BG, self.rect, border_radius=self.border_radius)

        # Border (highlighted when focused)
        border_col = COLOR_PRIMARY if self.is_focused else COLOR_CARD_BORDER
        border_w = 2 if self.is_focused else 1
        pygame.draw.rect(surface, border_col, self.rect, width=border_w, border_radius=self.border_radius)

        font = get_font(self.font_size)

        # Display text or placeholder
        display_str = ("*" * len(self.text)) if self.is_password else self.text
        if not display_str and not self.is_focused:
            # Placeholder
            txt_surf = font.render(self.placeholder, True, COLOR_TEXT_MUTED)
            surface.blit(txt_surf, (self.rect.x + 12, self.rect.centery - txt_surf.get_height() // 2))
        else:
            txt_surf = font.render(display_str, True, COLOR_TEXT_DARK)
            # Clip if too long
            text_x = self.rect.x + 12
            text_y = self.rect.centery - txt_surf.get_height() // 2
            surface.blit(txt_surf, (text_x, text_y))

            # Cursor
            if self.is_focused and self.show_cursor:
                cursor_x = text_x + txt_surf.get_width() + 2
                cursor_y1 = self.rect.centery - 10
                cursor_y2 = self.rect.centery + 10
                pygame.draw.line(surface, COLOR_PRIMARY, (cursor_x, cursor_y1), (cursor_x, cursor_y2), 2)
