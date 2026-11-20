"""
Inventory Screen for LittleLife Pygame UI.
Displays owned items grid, item quantities, descriptions, effects,
and an interactive Use button to apply items to the pet.
"""
from typing import Callable, Dict, Tuple
import pygame
try:
    from ..theme import (
        COLOR_PRIMARY,
        COLOR_PRIMARY_HOVER,
        COLOR_PRIMARY_DARK,
        COLOR_ACCENT,
        COLOR_TEXT_DARK,
        COLOR_TEXT_MUTED,
        COLOR_CARD_BG,
        COLOR_CARD_BORDER,
        COLOR_DISABLED,
        COLOR_DISABLED_TEXT
    )
    from ..components import Card, Button, draw_text
    from ..mock_data import InventoryItem
except ImportError:
    from theme import (
        COLOR_PRIMARY,
        COLOR_PRIMARY_HOVER,
        COLOR_PRIMARY_DARK,
        COLOR_ACCENT,
        COLOR_TEXT_DARK,
        COLOR_TEXT_MUTED,
        COLOR_CARD_BG,
        COLOR_CARD_BORDER,
        COLOR_DISABLED,
        COLOR_DISABLED_TEXT
    )
    from components import Card, Button, draw_text
    from mock_data import InventoryItem


class InventoryScreen:
    """Screen for viewing owned items and using them on the pet."""
    def __init__(
        self,
        on_use_item: Callable[[int], Tuple[bool, str]],
        show_notification: Callable[[str, str], None]
    ):
        self.on_use_item = on_use_item
        self.show_notification = show_notification

        # Main Inventory Container Card
        self.main_card = Card(
            (50, 90, 860, 480),
            title="Backpack & Supplies",
            subtitle="View your stored food, medicines, and toys. Use them to care for your pet"
        )

        self.use_buttons: dict[int, Button] = {}

    def _trigger_use(self, item_id: int):
        success, msg = self.on_use_item(item_id)
        self.show_notification(msg, "success" if success else "error")

    def handle_event(self, event: pygame.event.Event):
        for btn in self.use_buttons.values():
            btn.handle_event(event)

    def update(self, dt: float):
        pass

    def _draw_item_icon(self, surface: pygame.Surface, item_type: str, rect: pygame.Rect):
        """Draws clean procedural iconography according to item type."""
        pygame.draw.rect(surface, (244, 241, 235), rect, border_radius=8)
        pygame.draw.rect(surface, (230, 225, 218), rect, width=1, border_radius=8)

        cx, cy = rect.center
        if item_type == "food":
            pygame.draw.circle(surface, (220, 160, 100), (cx, cy), 14)
            pygame.draw.circle(surface, (130, 80, 45), (cx - 4, cy - 4), 2)
            pygame.draw.circle(surface, (130, 80, 45), (cx + 5, cy - 2), 2)
            pygame.draw.circle(surface, (130, 80, 45), (cx - 1, cy + 5), 2)
        elif item_type == "toy":
            pygame.draw.circle(surface, (245, 140, 110), (cx, cy), 14)
            pygame.draw.line(surface, (255, 220, 150), (cx - 13, cy), (cx + 13, cy), 4)
        elif item_type == "medicine":
            bottle_rect = pygame.Rect(cx - 8, cy - 6, 16, 19)
            pygame.draw.rect(surface, (120, 205, 140), bottle_rect, border_radius=3)
            pygame.draw.rect(surface, (90, 165, 110), (cx - 5, cy - 11, 10, 5), border_radius=2)
            pygame.draw.line(surface, (255, 255, 255), (cx, cy - 2), (cx, cy + 7), 2)
            pygame.draw.line(surface, (255, 255, 255), (cx - 4, cy + 2), (cx + 4, cy + 2), 2)
        else:
            pygame.draw.circle(surface, (150, 175, 240), (cx, cy + 3), 11)
            pygame.draw.rect(surface, (190, 150, 220), (cx - 4, cy - 10, 8, 8), border_radius=2)

    def render(self, surface: pygame.Surface, inventory: Dict[int, InventoryItem]):
        self.main_card.render(surface)

        self.use_buttons.clear()

        # If backpack is empty
        if not inventory:
            empty_box = pygame.Rect(320, 240, 320, 120)
            pygame.draw.rect(surface, (248, 246, 242), empty_box, border_radius=12)
            pygame.draw.rect(surface, (230, 225, 218), empty_box, width=1, border_radius=12)
            draw_text(surface, "Your backpack is empty!", empty_box.center, font_size=16, color=COLOR_TEXT_MUTED, bold=True, align="center")
            draw_text(surface, "Visit the Shop to buy food and supplies.", (empty_box.centerx, empty_box.centery + 24), font_size=13, color=COLOR_TEXT_MUTED, align="center")
            return

        # 3-column grid for inventory cards
        start_x = 75
        start_y = 150
        card_w = 250
        card_h = 160
        gap_x = 20
        gap_y = 20

        inv_items_list = list(inventory.values())

        for idx, inv_item in enumerate(inv_items_list):
            col = idx % 3
            row = idx // 3
            x = start_x + col * (card_w + gap_x)
            y = start_y + row * (card_h + gap_y)

            item = inv_item.item
            item_box = pygame.Rect(x, y, card_w, card_h)

            pygame.draw.rect(surface, (252, 251, 248), item_box, border_radius=10)
            pygame.draw.rect(surface, COLOR_CARD_BORDER, item_box, width=1, border_radius=10)

            # Icon Box
            icon_rect = pygame.Rect(x + 12, y + 14, 44, 44)
            self._draw_item_icon(surface, item.item_type, icon_rect)

            # Item Name & Type
            draw_text(surface, item.name, (x + 64, y + 14), font_size=15, color=COLOR_TEXT_DARK, bold=True)
            draw_text(surface, item.item_type.capitalize(), (x + 64, y + 36), font_size=11, color=COLOR_TEXT_MUTED)

            # Quantity Badge in top-right corner of card
            qty_rect = pygame.Rect(x + card_w - 56, y + 14, 44, 22)
            pygame.draw.rect(surface, (235, 243, 238), qty_rect, border_radius=11)
            pygame.draw.rect(surface, COLOR_PRIMARY, qty_rect, width=1, border_radius=11)
            draw_text(surface, f"x{inv_item.quantity}", qty_rect.center, font_size=12, color=COLOR_PRIMARY_DARK, bold=True, align="center")

            # Effect pill
            effect_badge = f"+{item.effect_value} {item.effect_type.capitalize()}"
            effect_rect = pygame.Rect(x + 12, y + 70, 120, 22)
            pygame.draw.rect(surface, (238, 244, 240), effect_rect, border_radius=11)
            draw_text(surface, effect_badge, effect_rect.center, font_size=11, color=COLOR_PRIMARY_DARK, bold=True, align="center")

            # Description (word truncated)
            draw_text(surface, item.description, (x + 12, y + 100), font_size=11, color=COLOR_TEXT_MUTED)

            # Use button
            btn_rect = pygame.Rect(x + card_w - 95, y + card_h - 44, 83, 32)
            iid = inv_item.item_id
            btn = Button(
                btn_rect,
                "Use",
                on_click=lambda i=iid: self._trigger_use(i),
                bg_color=COLOR_PRIMARY,
                hover_color=COLOR_PRIMARY_HOVER,
                font_size=13
            )
            self.use_buttons[iid] = btn
            btn.render(surface)
