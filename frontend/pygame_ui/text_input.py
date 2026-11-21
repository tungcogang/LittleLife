"""
Component TextInput cho Pygame UI.

Ô nhập liệu dùng chung cho Register, Habit, Pet Adoption... Nhận văn bản đã
được IME/OS hợp thành qua sự kiện ``TEXTINPUT`` (VNI, Telex, tiếng Việt có dấu)
và hiển thị tạm chuỗi đang soạn qua ``TEXTEDITING``. Các phím điều khiển như
Enter, Backspace, Escape vẫn được xử lý qua ``KEYDOWN``.
"""
from typing import Tuple
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
    """Ô nhập văn bản hỗ trợ focus, placeholder, con trỏ, che mật khẩu và IME."""
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

        # Chuỗi IME đang soạn (chưa commit), chỉ hiển thị tạm và không lưu vào text.
        self.composition = ""

    def clear(self):
        """Xóa toàn bộ nội dung đã nhập và cả phần đang soạn của IME."""
        self.text = ""
        self.composition = ""

    def _activate_text_input(self):
        """Bật text input và đặt cửa sổ candidate của IME gần ô đang focus."""
        try:
            pygame.key.start_text_input()
            pygame.key.set_text_input_rect(self.rect)
        except pygame.error:
            # Một số video driver (headless/dummy) không hỗ trợ text input.
            pass

    def _insert_text(self, text: str):
        """Chèn đoạn text đã commit, tôn trọng max_length và bỏ ký tự điều khiển."""
        if not text:
            return

        filtered = "".join(ch for ch in text if ch.isprintable())
        if not filtered:
            return

        remaining = self.max_length - len(self.text)
        if remaining <= 0:
            return

        self.text += filtered[:remaining]
        self.composition = ""

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Xử lý focus, văn bản IME và phím điều khiển.

        Trả về True khi nhấn Enter trên ô đang focus và IME không còn soạn dở,
        để màn hình cha quyết định submit/chuyển ô.
        """
        # Click chuột: cập nhật focus và vị trí candidate của IME.
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            was_focused = self.is_focused
            self.is_focused = self.rect.collidepoint(event.pos)
            self.cursor_timer = 0.0
            self.show_cursor = True

            if self.is_focused:
                self._activate_text_input()
            elif was_focused:
                self.composition = ""

            return False

        if not self.is_focused:
            return False

        # Văn bản đã được IME/OS commit (ví dụ: "Uống", "nước", "tung").
        if event.type == pygame.TEXTINPUT:
            self.composition = ""
            self._insert_text(getattr(event, "text", "") or "")
            return False

        # Chuỗi IME đang soạn: chỉ hiển thị tạm, chưa ghi vào buffer.
        if event.type == pygame.TEXTEDITING:
            self.composition = getattr(event, "text", "") or ""
            return False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                # Không submit khi IME còn đang soạn; Enter có thể là phím chọn.
                return not self.composition

            if event.key in (pygame.K_BACKSPACE, pygame.K_DELETE):
                # Khi IME đang soạn, để IME xử lý phím xóa; không xóa text đã commit.
                if not self.composition:
                    self.text = self.text[:-1]
            elif event.key == pygame.K_ESCAPE:
                self.is_focused = False
                self.composition = ""

            # Không dùng event.unicode ở đây: TEXTINPUT mới là nguồn văn bản
            # chính thức, tránh chèn trùng khi IME gửi cả KEYDOWN và TEXTINPUT.

        return False

    def update(self, dt: float):
        if self.is_focused:
            # Cập nhật vị trí danh sách gợi ý/candidate của IME theo ô hiện tại.
            try:
                pygame.key.set_text_input_rect(self.rect)
            except pygame.error:
                pass

            self.cursor_timer += dt
            if self.cursor_timer >= 0.5:
                self.cursor_timer = 0.0
                self.show_cursor = not self.show_cursor
        else:
            self.show_cursor = False
            self.composition = ""

    def render(self, surface: pygame.Surface):
        # Nền
        pygame.draw.rect(surface, COLOR_CARD_BG, self.rect, border_radius=self.border_radius)

        # Viền (đổi màu khi được focus)
        border_col = COLOR_PRIMARY if self.is_focused else COLOR_CARD_BORDER
        border_w = 2 if self.is_focused else 1
        pygame.draw.rect(surface, border_col, self.rect, width=border_w, border_radius=self.border_radius)

        font = get_font(self.font_size)

        # Text đã commit + chuỗi đang soạn của IME; che mật khẩu nếu cần.
        display_str = self.text + self.composition
        if self.is_password:
            display_str = "*" * len(display_str)

        if not display_str and not self.is_focused:
            # Hiển thị placeholder
            txt_surf = font.render(self.placeholder, True, COLOR_TEXT_MUTED)
            surface.blit(txt_surf, (self.rect.x + 12, self.rect.centery - txt_surf.get_height() // 2))
        else:
            txt_surf = font.render(display_str, True, COLOR_TEXT_DARK)
            # Cắt bớt nếu quá dài
            text_x = self.rect.x + 12
            text_y = self.rect.centery - txt_surf.get_height() // 2
            surface.blit(txt_surf, (text_x, text_y))

            # Con trỏ
            if self.is_focused and self.show_cursor:
                cursor_x = text_x + txt_surf.get_width() + 2
                cursor_y1 = self.rect.centery - 10
                cursor_y2 = self.rect.centery + 10
                pygame.draw.line(surface, COLOR_PRIMARY, (cursor_x, cursor_y1), (cursor_x, cursor_y2), 2)
