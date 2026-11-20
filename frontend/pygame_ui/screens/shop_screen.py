"""
Shop Screen for LittleLife Pygame UI.
Displays item cards, prices, descriptions, effects, current coin balance,
and interactive Buy buttons with mock transaction feedback.
"""
from typing import Callable, List, Tuple
import pygame
try:
    from ..theme import (
        COLOR_PRIMARY,
        COLOR_PRIMARY_HOVER,
        COLOR_PRIMARY_DARK,
        COLOR_ACCENT,
        COLOR_ACCENT_HOVER,
        COLOR_COIN,
        COLOR_COIN_BG,
        COLOR_COIN_BORDER,
        COLOR_TEXT_DARK,
        COLOR_TEXT_MUTED,
        COLOR_TEXT_LIGHT,
        COLOR_CARD_BG,
        COLOR_CARD_BORDER,
        COLOR_DISABLED,
        COLOR_DISABLED_TEXT
    )
    from ..components import Card, Button, draw_text
    from ..mock_data import ShopItem
except ImportError:
    from theme import (
        COLOR_PRIMARY,
        COLOR_PRIMARY_HOVER,
        COLOR_PRIMARY_DARK,
        COLOR_ACCENT,
        COLOR_ACCENT_HOVER,
        COLOR_COIN,
        COLOR_COIN_BG,
        COLOR_COIN_BORDER,
        COLOR_TEXT_DARK,
        COLOR_TEXT_MUTED,
        COLOR_TEXT_LIGHT,
        COLOR_CARD_BG,
        COLOR_CARD_BORDER,
        COLOR_DISABLED,
        COLOR_DISABLED_TEXT
    )
    from components import Card, Button, draw_text
    from mock_data import ShopItem


class ShopScreen:
    """Screen for browsing shop items and purchasing supplies for the pet."""
    def __init__(
        self,
        on_buy_item: Callable[[int], Tuple[bool, str]],
        show_notification: Callable[[str, str], None]
    ):
        self.on_buy_item = on_buy_item
        self.show_notification = show_notification

        # Main Shop Container Card
        self.main_card = Card(
            (50, 90, 860, 480),
            title="General Store",
            subtitle="Purchase nutritious treats, fun toys, and rejuvenating remedies"
        )

        self.buy_buttons: dict[int, Button] = {}

    def _trigger_buy(self, item_id: int):
        success, msg = self.on_buy_item(item_id)
        self.show_notification(msg, "success" if success else "error")

    def handle_event(self, event: pygame.event.Event):
        for btn in self.buy_buttons.values():
            btn.handle_event(event)

    def update(self, dt: float):
        pass

    def _draw_item_icon(self, surface: pygame.Surface, item_type: str, rect: pygame.Rect):
        """Draws clean procedural iconography according to item type."""
        pygame.draw.rect(surface, (244, 241, 235), rect, border_radius=8)
        pygame.draw.rect(surface, (230, 225, 218), rect, width=1, border_radius=8)

        cx, cy = rect.center
        if item_type == "food":
            # Cute biscuit / cookie shape
            pygame.draw.circle(surface, (220, 160, 100), (cx, cy), 14)
            # Chocolate chips
            pygame.draw.circle(surface, (130, 80, 45), (cx - 4, cy - 4), 2)
            pygame.draw.circle(surface, (130, 80, 45), (cx + 5, cy - 2), 2)
            pygame.draw.circle(surface, (130, 80, 45), (cx - 1, cy + 5), 2)
        elif item_type == "toy":
            # Playful ball with stripe
            pygame.draw.circle(surface, (245, 140, 110), (cx, cy), 14)
            pygame.draw.line(surface, (255, 220, 150), (cx - 13, cy), (cx + 13, cy), 4)
        elif item_type == "medicine":
            # Pill/tonic bottle
            bottle_rect = pygame.Rect(cx - 8, cy - 6, 16, 19)
            pygame.draw.rect(surface, (120, 205, 140), bottle_rect, border_radius=3)
            # Cap
            pygame.draw.rect(surface, (90, 165, 110), (cx - 5, cy - 11, 10, 5), border_radius=2)
            # Cross on bottle
            pygame.draw.line(surface, (255, 255, 255), (cx, cy - 2), (cx, cy + 7), 2)
            pygame.draw.line(surface, (255, 255, 255), (cx - 4, cy + 2), (cx + 4, cy + 2), 2)
        else:
            # Potion / elixir bottle
            pygame.draw.circle(surface, (150, 175, 240), (cx, cy + 3), 11)
            pygame.draw.rect(surface, (190, 150, 220), (cx - 4, cy - 10, 8, 8), border_radius=2)

    def render(self, surface: pygame.Surface, shop_items: List[ShopItem], user_coins: int):
        self.main_card.render(surface)

        # 2-column or 3-column grid of item cards
        start_x = 75
        start_y = 150
        card_w = 250
        card_h = 180
        gap_x = 20
        gap_y = 20

        self.buy_buttons.clear()

        for idx, item in enumerate(shop_items):
            col = idx % 3
            row = idx // 3
            x = start_x + col * (card_w + gap_x)
            y = start_y + row * (card_h + gap_y)

            item_box = pygame.Rect(x, y, card_w, card_h)
            # Inner item card
            pygame.draw.rect(surface, (252, 251, 248), item_box, border_radius=10)
            pygame.draw.rect(surface, COLOR_CARD_BORDER, item_box, width=1, border_radius=10)

            # Icon Box
            icon_rect = pygame.Rect(x + 12, y + 14, 44, 44)
            self._draw_item_icon(surface, item.item_type, icon_rect)

            # Item Name & Type Tag
            draw_text(surface, item.name, (x + 64, y + 14), font_size=15, color=COLOR_TEXT_DARK, bold=True)
            draw_text(surface, item.item_type.capitalize(), (x + 64, y + 36), font_size=11, color=COLOR_TEXT_MUTED)

            # Description (word wrapped or truncated cleanly)
            draw_text(surface, item.description, (x + 12, y + 68), font_size=11, color=COLOR_TEXT_MUTED)

            # Effect pill
            effect_badge = f"+{item.effect_value} {item.effect_type.capitalize()}"
            effect_rect = pygame.Rect(x + 12, y + 96, 120, 22)
            pygame.draw.rect(surface, (238, 244, 240), effect_rect, border_radius=11)
            draw_text(surface, effect_badge, effect_rect.center, font_size=11, color=COLOR_PRIMARY_DARK, bold=True, align="center")

            # Price & Buy Button
            # Price badge
            coin_icon_pos = (x + 22, y + 144)
            pygame.draw.circle(surface, COLOR_COIN, coin_icon_pos, 7)
            draw_text(surface, f"{item.price} coins", (x + 36, y + 137), font_size=13, color=COLOR_TEXT_DARK, bold=True)

            # Buy button
            can_afford = user_coins >= item.price
            btn_rect = pygame.Rect(x + 140, y + 130, 95, 34)
            iid = item.id

            btn = Button(
                btn_rect,
                "Buy",
                on_click=lambda i=iid: self._trigger_buy(i),
                enabled=can_afford,
                bg_color=COLOR_ACCENT,
                hover_color=COLOR_ACCENT_HOVER,
                font_size=13
            )
            self.buy_buttons[item.id] = btn
            btn.render(surface)
