"""
Các component UI dùng chung cho LittleLife Pygame UI.
Bao gồm Button, ProgressBar, Card, CoinDisplay, Banner/Notification và các hàm hỗ trợ render text.
"""
from typing import Callable, Optional, Tuple
import pygame
try:
    from .theme import (
        COLOR_PRIMARY,
        COLOR_PRIMARY_HOVER,
        COLOR_PRIMARY_DARK,
        COLOR_TEXT_LIGHT,
        COLOR_TEXT_DARK,
        COLOR_TEXT_MUTED,
        COLOR_CARD_BG,
        COLOR_CARD_BORDER,
        COLOR_COIN,
        COLOR_COIN_BG,
        COLOR_COIN_BORDER,
        COLOR_DISABLED,
        COLOR_DISABLED_TEXT,
        get_font
    )
except ImportError:
    from theme import (
        COLOR_PRIMARY,
        COLOR_PRIMARY_HOVER,
        COLOR_PRIMARY_DARK,
        COLOR_TEXT_LIGHT,
        COLOR_TEXT_DARK,
        COLOR_TEXT_MUTED,
        COLOR_CARD_BG,
        COLOR_CARD_BORDER,
        COLOR_COIN,
        COLOR_COIN_BG,
        COLOR_COIN_BORDER,
        COLOR_DISABLED,
        COLOR_DISABLED_TEXT,
        get_font
    )

def draw_text(
    surface: pygame.Surface,
    text: str,
    pos: Tuple[int, int],
    font_size: int = 18,
    color: Tuple[int, int, int] = COLOR_TEXT_DARK,
    bold: bool = False,
    align: str = "topleft"
) -> pygame.Rect:
    """Hàm phụ render text lên surface, hỗ trợ căn lề."""
    font = get_font(size=font_size, bold=bold)
    text_surf = font.render(str(text), True, color)
    rect = text_surf.get_rect()
    setattr(rect, align, pos)
    surface.blit(text_surf, rect)
    return rect


def fit_text(text: str, font_size: int, max_width: int, bold: bool = False) -> str:
    """Cắt bớt text kèm dấu ba chấm để không bao giờ tràn ra khỏi card."""
    font = get_font(size=font_size, bold=bold)
    text = str(text or "")
    if font.size(text)[0] <= max_width:
        return text

    ellipsis = "..."
    trimmed = text
    while trimmed and font.size(trimmed + ellipsis)[0] > max_width:
        trimmed = trimmed[:-1]

    return (trimmed.rstrip() + ellipsis) if trimmed else ellipsis


def draw_effect_badge(
    surface: pygame.Surface,
    text: str,
    pos: Tuple[int, int],
    max_width: int = 200,
    font_size: int = 11
) -> pygame.Rect:
    """Vẽ nhãn dạng viên thuốc chứa một hoặc hai hiệu ứng của item, vừa trong card."""
    display = fit_text(text, font_size, max_width - 20, bold=True)
    font = get_font(size=font_size, bold=True)
    width = min(max_width, max(90, font.size(display)[0] + 20))
    rect = pygame.Rect(pos[0], pos[1], width, 22)

    pygame.draw.rect(surface, (238, 244, 240), rect, border_radius=11)
    draw_text(
        surface,
        display,
        rect.center,
        font_size=font_size,
        color=COLOR_PRIMARY_DARK,
        bold=True,
        align="center"
    )
    return rect


class Button:
    """Component nút bấm tương tác dễ chịu với trạng thái hover, vô hiệu hóa và callback."""
    def __init__(
        self,
        rect: Tuple[int, int, int, int] | pygame.Rect,
        text: str,
        on_click: Optional[Callable[[], None]] = None,
        bg_color: Tuple[int, int, int] = COLOR_PRIMARY,
        hover_color: Optional[Tuple[int, int, int]] = COLOR_PRIMARY_HOVER,
        text_color: Tuple[int, int, int] = COLOR_TEXT_LIGHT,
        font_size: int = 16,
        border_radius: int = 8,
        enabled: bool = True
    ):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.on_click = on_click
        self.bg_color = bg_color
        self.hover_color = hover_color if hover_color else bg_color
        self.text_color = text_color
        self.font_size = font_size
        self.border_radius = border_radius
        self.enabled = enabled
        self.is_hovered = False

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Xử lý sự kiện di chuột và click. Trả về True nếu được click."""
        if not self.enabled:
            self.is_hovered = False
            return False

        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.on_click:
                    self.on_click()
                return True
        return False

    def render(self, surface: pygame.Surface):
        if not self.enabled:
            color = COLOR_DISABLED
            txt_color = COLOR_DISABLED_TEXT
        elif self.is_hovered:
            color = self.hover_color
            txt_color = self.text_color
        else:
            color = self.bg_color
            txt_color = self.text_color

        # Bóng đổ nhẹ tạo cảm giác có chiều sâu
        if self.enabled:
            shadow_rect = pygame.Rect(self.rect.x, self.rect.y + 2, self.rect.width, self.rect.height)
            pygame.draw.rect(surface, (215, 210, 200), shadow_rect, border_radius=self.border_radius)

        pygame.draw.rect(surface, color, self.rect, border_radius=self.border_radius)
        draw_text(surface, self.text, self.rect.center, font_size=self.font_size, color=txt_color, bold=True, align="center")


class ProgressBar:
    """Thanh tiến trình bo tròn dễ chịu, có nhãn và số liệu tùy chọn."""
    def __init__(
        self,
        rect: Tuple[int, int, int, int] | pygame.Rect,
        current_val: float,
        max_val: float = 100.0,
        fill_color: Tuple[int, int, int] = COLOR_PRIMARY,
        bg_color: Tuple[int, int, int] = (235, 230, 222),
        label: str = "",
        show_numbers: bool = True,
        border_radius: int = 6
    ):
        self.rect = pygame.Rect(rect)
        self.current_val = current_val
        self.max_val = max(1.0, float(max_val))
        self.fill_color = fill_color
        self.bg_color = bg_color
        self.label = label
        self.show_numbers = show_numbers
        self.border_radius = border_radius

    def render(self, surface: pygame.Surface):
        # Nhãn tiêu đề tùy chọn
        if self.label:
            draw_text(surface, self.label, (self.rect.x, self.rect.y - 18), font_size=13, color=COLOR_TEXT_MUTED, bold=True)
            if self.show_numbers:
                num_text = f"{int(self.current_val)}/{int(self.max_val)}"
                draw_text(surface, num_text, (self.rect.right, self.rect.y - 18), font_size=13, color=COLOR_TEXT_MUTED, bold=False, align="topright")

        # Rãnh nền
        pygame.draw.rect(surface, self.bg_color, self.rect, border_radius=self.border_radius)

        # Phần rãnh đã lấp đầy
        pct = max(0.0, min(1.0, self.current_val / self.max_val))
        fill_width = int(self.rect.width * pct)
        if fill_width > 0:
            fill_rect = pygame.Rect(self.rect.x, self.rect.y, fill_width, self.rect.height)
            pygame.draw.rect(surface, self.fill_color, fill_rect, border_radius=self.border_radius)

        # Đường viền ngoài
        pygame.draw.rect(surface, (220, 214, 204), self.rect, width=1, border_radius=self.border_radius)


class Card:
    """Khung card/panel dễ chịu với viền mềm và tiêu đề tùy chọn."""
    def __init__(
        self,
        rect: Tuple[int, int, int, int] | pygame.Rect,
        bg_color: Tuple[int, int, int] = COLOR_CARD_BG,
        border_color: Tuple[int, int, int] = COLOR_CARD_BORDER,
        border_radius: int = 12,
        title: str = "",
        subtitle: str = ""
    ):
        self.rect = pygame.Rect(rect)
        self.bg_color = bg_color
        self.border_color = border_color
        self.border_radius = border_radius
        self.title = title
        self.subtitle = subtitle

    def render(self, surface: pygame.Surface):
        # Bóng đổ mềm
        shadow_rect = pygame.Rect(self.rect.x, self.rect.y + 3, self.rect.width, self.rect.height)
        pygame.draw.rect(surface, (230, 224, 215), shadow_rect, border_radius=self.border_radius)

        # Nền chính
        pygame.draw.rect(surface, self.bg_color, self.rect, border_radius=self.border_radius)
        # Viền
        pygame.draw.rect(surface, self.border_color, self.rect, width=1, border_radius=self.border_radius)

        # Phần tiêu đề & phụ đề tùy chọn
        if self.title:
            draw_text(surface, self.title, (self.rect.x + 16, self.rect.y + 14), font_size=18, color=COLOR_TEXT_DARK, bold=True)
            if self.subtitle:
                draw_text(surface, self.subtitle, (self.rect.x + 16, self.rect.y + 36), font_size=13, color=COLOR_TEXT_MUTED)


class CoinDisplay:
    """Huy hiệu hiển thị Coin với icon và số dư đã định dạng."""
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        self.width = 130
        self.height = 36

    def render(self, surface: pygame.Surface, coins: int):
        rect = pygame.Rect(self.x, self.y, self.width, self.height)
        # Nền viên thuốc hiển thị Coin
        pygame.draw.rect(surface, COLOR_COIN_BG, rect, border_radius=18)
        pygame.draw.rect(surface, COLOR_COIN_BORDER, rect, width=1, border_radius=18)

        # Icon đồng xu vàng nhỏ hình tròn
        coin_center = (self.x + 18, self.y + 18)
        pygame.draw.circle(surface, COLOR_COIN, coin_center, 10)
        pygame.draw.circle(surface, (217, 119, 6), coin_center, 10, width=1)
        draw_text(surface, "$", (coin_center[0], coin_center[1] + 1), font_size=13, color=(255, 255, 255), bold=True, align="center")

        # Chữ hiển thị số dư
        draw_text(surface, f"{coins:,}", (self.x + 36, self.y + 9), font_size=16, color=COLOR_TEXT_DARK, bold=True)


class NotificationBanner:
    """Banner thông báo dạng nổi hoặc cố định (success, error, info), tự động ẩn."""
    def __init__(self):
        self.message: str = ""
        self.msg_type: str = "info"  # "success", "error", "info"
        self.timer: float = 0.0

    def show(self, message: str, msg_type: str = "info", duration: float = 3.0):
        self.message = message
        self.msg_type = msg_type
        self.timer = duration

    def update(self, dt: float):
        if self.timer > 0:
            self.timer -= dt
            if self.timer <= 0:
                self.message = ""

    def render(self, surface: pygame.Surface, center_x: int, top_y: int):
        if not self.message or self.timer <= 0:
            return

        colors = {
            "success": ((220, 245, 225), (100, 185, 120), (45, 90, 55)),
            "error": ((254, 226, 226), (239, 68, 68), (153, 27, 27)),
            "info": ((224, 242, 254), (56, 189, 248), (7, 89, 133)),
        }
        bg, border, text_col = colors.get(self.msg_type, colors["info"])

        font = get_font(14, bold=True)
        text_surf = font.render(self.message, True, text_col)
        pad_x, pad_y = 20, 10
        rect = pygame.Rect(0, 0, text_surf.get_width() + pad_x * 2, text_surf.get_height() + pad_y * 2)
        rect.centerx = center_x
        rect.top = top_y

        pygame.draw.rect(surface, bg, rect, border_radius=10)
        pygame.draw.rect(surface, border, rect, width=1, border_radius=10)
        surface.blit(text_surf, (rect.x + pad_x, rect.y + pad_y))
