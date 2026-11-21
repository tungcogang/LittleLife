"""
Màn hình Shop cho LittleLife Pygame UI.
Hiển thị các card item, giá, mô tả, hiệu ứng, số lượng đang sở hữu,
số dư Coin hiện tại và các nút Buy tương tác nối với Store API của backend.
"""
from typing import Callable, Dict, List, Tuple
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
    from ..components import Card, Button, draw_text, fit_text, draw_effect_badge
    from ..mock_data import ShopItem, InventoryItem
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
    from components import Card, Button, draw_text, fit_text, draw_effect_badge
    from mock_data import ShopItem, InventoryItem


class ShopScreen:
    """Màn hình xem các item trong shop và mua vật phẩm cho pet."""
    def __init__(
        self,
        on_buy_item: Callable[[int], Tuple[bool, str]],
        show_notification: Callable[[str, str], None]
    ):
        self.on_buy_item = on_buy_item
        self.show_notification = show_notification

        # Card khung chính của Shop
        self.main_card = Card(
            (50, 90, 860, 480),
            title="General Store",
            subtitle="Purchase nutritious treats, fun toys, and rejuvenating remedies"
        )

        self.buy_buttons: dict[int, Button] = {}

        # Chặn lần mua thứ hai trong cùng một loạt sự kiện click cho tới khi
        # UI render lại với số dư Coin và Backpack đã cập nhật.
        self.in_flight_item_id = None

    def on_show(self):
        """Xóa trạng thái tạm của button khi mở màn hình."""
        self.in_flight_item_id = None

    def _trigger_buy(self, item_id: int):
        if self.in_flight_item_id is not None:
            return

        self.in_flight_item_id = item_id
        success, msg = self.on_buy_item(item_id)
        self.show_notification(msg, "success" if success else "error")

    def handle_event(self, event: pygame.event.Event):
        for btn in self.buy_buttons.values():
            btn.handle_event(event)

    def update(self, dt: float):
        pass

    def _draw_item_icon(self, surface: pygame.Surface, item_type: str, rect: pygame.Rect):
        """Vẽ icon đơn giản bằng hình học theo loại item."""
        pygame.draw.rect(surface, (244, 241, 235), rect, border_radius=8)
        pygame.draw.rect(surface, (230, 225, 218), rect, width=1, border_radius=8)

        cx, cy = rect.center
        if item_type == "food":
            # Hình bánh quy dễ thương
            pygame.draw.circle(surface, (220, 160, 100), (cx, cy), 14)
            # Hạt chocolate
            pygame.draw.circle(surface, (130, 80, 45), (cx - 4, cy - 4), 2)
            pygame.draw.circle(surface, (130, 80, 45), (cx + 5, cy - 2), 2)
            pygame.draw.circle(surface, (130, 80, 45), (cx - 1, cy + 5), 2)
        elif item_type == "toy":
            # Quả bóng tinh nghịch có sọc
            pygame.draw.circle(surface, (245, 140, 110), (cx, cy), 14)
            pygame.draw.line(surface, (255, 220, 150), (cx - 13, cy), (cx + 13, cy), 4)
        elif item_type == "medicine":
            # Lọ thuốc/viên thuốc
            bottle_rect = pygame.Rect(cx - 8, cy - 6, 16, 19)
            pygame.draw.rect(surface, (120, 205, 140), bottle_rect, border_radius=3)
            # Nắp lọ
            pygame.draw.rect(surface, (90, 165, 110), (cx - 5, cy - 11, 10, 5), border_radius=2)
            # Dấu thập trên thân lọ
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
            # Lọ potion / elixir
            pygame.draw.circle(surface, (150, 175, 240), (cx, cy + 3), 11)
            pygame.draw.rect(surface, (190, 150, 220), (cx - 4, cy - 10, 8, 8), border_radius=2)

    def render(
        self,
        surface: pygame.Surface,
        shop_items: List[ShopItem],
        user_coins: int,
        inventory: Dict[int, InventoryItem] | None = None
    ):
        self.main_card.render(surface)

        inventory = inventory or {}

        # Cho phép lượt click tiếp theo mua tiếp khi frame này đã hiển thị.
        self.in_flight_item_id = None

        # Lưới 2 cột hoặc 3 cột các card item
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
            # Card item bên trong
            pygame.draw.rect(surface, (252, 251, 248), item_box, border_radius=10)
            pygame.draw.rect(surface, COLOR_CARD_BORDER, item_box, width=1, border_radius=10)

            # Khung icon
            icon_rect = pygame.Rect(x + 12, y + 14, 44, 44)
            self._draw_item_icon(surface, item.item_type, icon_rect)

            # Tên item & nhãn loại (số lượng đang sở hữu nằm trên dòng loại)
            draw_text(surface, fit_text(item.name, 15, 160, bold=True), (x + 64, y + 14), font_size=15, color=COLOR_TEXT_DARK, bold=True)
            draw_text(surface, item.item_type.capitalize(), (x + 64, y + 36), font_size=11, color=COLOR_TEXT_MUTED)

            owned = inventory.get(item.id)
            if owned and owned.quantity > 0:
                draw_text(surface, f"Owned x{owned.quantity}", (x + card_w - 12, y + 36), font_size=10, color=COLOR_PRIMARY, bold=True, align="topright")

            # Mô tả (được cắt để text dài không tràn khỏi card)
            draw_text(surface, fit_text(item.description, 11, card_w - 24), (x + 12, y + 68), font_size=11, color=COLOR_TEXT_MUTED)

            # Nhãn hiệu ứng (vừa một hoặc hai hiệu ứng)
            draw_effect_badge(
                surface,
                item.effect_summary(),
                (x + 12, y + 96),
                max_width=card_w - 24
            )

            # Giá & nút Buy
            # Nhãn giá
            coin_icon_pos = (x + 22, y + 144)
            pygame.draw.circle(surface, COLOR_COIN, coin_icon_pos, 7)
            draw_text(surface, f"{item.price} coins", (x + 36, y + 137), font_size=13, color=COLOR_TEXT_DARK, bold=True)

            # Nút Buy
            can_afford = user_coins >= item.price
            is_loading = (self.in_flight_item_id == item.id)
            btn_rect = pygame.Rect(x + 140, y + 130, 95, 34)
            iid = item.id

            btn = Button(
                btn_rect,
                "Buying..." if is_loading else "Buy",
                on_click=lambda i=iid: self._trigger_buy(i),
                enabled=can_afford and not is_loading,
                bg_color=COLOR_ACCENT,
                hover_color=COLOR_ACCENT_HOVER,
                font_size=12 if is_loading else 13
            )
            self.buy_buttons[item.id] = btn
            btn.render(surface)
