"""
Màn hình Backpack cho LittleLife Pygame UI.
Hiển thị lưới các item đang sở hữu, số lượng, mô tả, hiệu ứng,
và nút Use tương tác để tiêu thụ item thông qua backend.
"""
from typing import Callable, Dict, Optional, Tuple
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
    from ..components import Card, Button, draw_text, fit_text, draw_effect_badge
    from ..mock_data import InventoryItem, PetState
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
    from components import Card, Button, draw_text, fit_text, draw_effect_badge
    from mock_data import InventoryItem, PetState


class InventoryScreen:
    """Màn hình xem các item đang sở hữu và sử dụng chúng cho pet."""
    def __init__(
        self,
        on_use_item: Callable[[int], Tuple[bool, str]],
        show_notification: Callable[[str, str], None]
    ):
        self.on_use_item = on_use_item
        self.show_notification = show_notification

        # Card khung chính của Backpack
        self.main_card = Card(
            (50, 90, 860, 480),
            title="Backpack & Supplies",
            subtitle="View your stored food, medicines, and toys. Use them to care for your pet"
        )

        self.use_buttons: dict[int, Button] = {}

        # Chặn lần dùng item thứ hai trong cùng một loạt sự kiện click.
        self.in_flight_item_id = None

    def on_show(self):
        """Xóa trạng thái tạm của button khi mở màn hình."""
        self.in_flight_item_id = None

    def _trigger_use(self, item_id: int):
        if self.in_flight_item_id is not None:
            return

        self.in_flight_item_id = item_id
        success, msg = self.on_use_item(item_id)
        self.show_notification(msg, "success" if success else "error")

    def handle_event(self, event: pygame.event.Event):
        for btn in self.use_buttons.values():
            btn.handle_event(event)

    def update(self, dt: float):
        pass

    def _draw_item_icon(self, surface: pygame.Surface, item_type: str, rect: pygame.Rect):
        """Vẽ icon đơn giản bằng hình học theo loại item."""
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
        elif item_type == "comfort":
            # Gối mềm cho item Cozy Pillow
            pillow_rect = pygame.Rect(cx - 15, cy - 11, 30, 22)
            pygame.draw.rect(surface, (204, 190, 238), pillow_rect, border_radius=7)
            pygame.draw.rect(surface, (167, 151, 205), pillow_rect, width=1, border_radius=7)
            pygame.draw.line(surface, (183, 168, 223), (cx - 9, cy - 2), (cx + 9, cy - 2), 1)
            pygame.draw.circle(surface, (238, 232, 250), (cx - 8, cy + 6), 2)
            pygame.draw.circle(surface, (238, 232, 250), (cx + 7, cy - 6), 2)
        else:
            pygame.draw.circle(surface, (150, 175, 240), (cx, cy + 3), 11)
            pygame.draw.rect(surface, (190, 150, 220), (cx - 4, cy - 10, 8, 8), border_radius=2)

    def render(
        self,
        surface: pygame.Surface,
        inventory: Dict[int, InventoryItem],
        pet: Optional[PetState] = None
    ):
        self.main_card.render(surface)

        self.use_buttons.clear()

        # Cho phép lượt click tiếp theo dùng item khác khi frame này đã hiển thị.
        self.in_flight_item_id = None

        # Nếu Backpack trống
        if not inventory:
            empty_box = pygame.Rect(320, 240, 320, 120)
            pygame.draw.rect(surface, (248, 246, 242), empty_box, border_radius=12)
            pygame.draw.rect(surface, (230, 225, 218), empty_box, width=1, border_radius=12)
            draw_text(surface, "Your backpack is empty!", empty_box.center, font_size=16, color=COLOR_TEXT_MUTED, bold=True, align="center")
            draw_text(surface, "Visit the Store to buy food and supplies.", (empty_box.centerx, empty_box.centery + 24), font_size=13, color=COLOR_TEXT_MUTED, align="center")
            return

        # Lưới 3 cột cho các card item trong Backpack
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

            # Khung icon
            icon_rect = pygame.Rect(x + 12, y + 14, 44, 44)
            self._draw_item_icon(surface, item.item_type, icon_rect)

            # Tên & loại item
            draw_text(surface, fit_text(item.name, 15, 150, bold=True), (x + 64, y + 14), font_size=15, color=COLOR_TEXT_DARK, bold=True)
            draw_text(surface, item.item_type.capitalize(), (x + 64, y + 36), font_size=11, color=COLOR_TEXT_MUTED)

            # Huy hiệu số lượng ở góc trên bên phải card
            qty_rect = pygame.Rect(x + card_w - 56, y + 14, 44, 22)
            pygame.draw.rect(surface, (235, 243, 238), qty_rect, border_radius=11)
            pygame.draw.rect(surface, COLOR_PRIMARY, qty_rect, width=1, border_radius=11)
            draw_text(surface, f"x{inv_item.quantity}", qty_rect.center, font_size=12, color=COLOR_PRIMARY_DARK, bold=True, align="center")

            # Nhãn hiệu ứng (vừa một hoặc hai hiệu ứng)
            draw_effect_badge(
                surface,
                item.effect_summary(),
                (x + 12, y + 70),
                max_width=card_w - 24
            )

            # Mô tả (được cắt để text dài không tràn khỏi card)
            draw_text(surface, fit_text(item.description, 11, card_w - 24), (x + 12, y + 100), font_size=11, color=COLOR_TEXT_MUTED)

            # Chỉ chặn dùng item khi mọi chỉ số mà item tác động đều đã đầy,
            # giống cách backend kiểm tra, tránh lãng phí item.
            effects = item.get_effects()
            at_max = (
                pet is not None
                and bool(effects)
                and all(getattr(pet, effect_type, 0) >= 100 for effect_type, _ in effects)
            )
            has_pet = pet is not None
            is_loading = (self.in_flight_item_id == inv_item.item_id)
            can_use = has_pet and not at_max and not is_loading

            btn_rect = pygame.Rect(x + card_w - 95, y + card_h - 44, 83, 32)
            iid = inv_item.item_id

            if at_max:
                button_text = "Full"
            elif not has_pet:
                button_text = "No Pet"
            elif is_loading:
                button_text = "Using..."
            else:
                button_text = "Use"

            btn = Button(
                btn_rect,
                button_text,
                on_click=lambda i=iid: self._trigger_use(i),
                enabled=can_use,
                bg_color=COLOR_PRIMARY,
                hover_color=COLOR_PRIMARY_HOVER,
                font_size=12
            )
            self.use_buttons[iid] = btn
            btn.render(surface)
