"""
Màn hình Habit cho LittleLife Pygame UI.
Hiển thị danh sách habit hằng ngày, trạng thái hoàn thành, các nút hoàn thành và tổng kết tiến độ trong ngày.
Đồng thời cho phép người chơi tạo habit mới, được backend lưu lại ở Online Mode.
Hoạt động với cả dữ liệu backend thật (GET /habits/) và mô phỏng offline cục bộ.
"""
from typing import Callable, List, Tuple
import pygame
try:
    from ..theme import (
        COLOR_PRIMARY,
        COLOR_PRIMARY_HOVER,
        COLOR_PRIMARY_DARK,
        COLOR_ACCENT,
        COLOR_SUCCESS,
        COLOR_TEXT_DARK,
        COLOR_TEXT_MUTED,
        COLOR_TEXT_LIGHT,
        COLOR_CARD_BG,
        COLOR_CARD_BORDER,
        COLOR_DISABLED,
        COLOR_DISABLED_TEXT,
        COLOR_DANGER
    )
    from ..components import Card, Button, ProgressBar, draw_text, fit_text
    from ..text_input import TextInput
    from ..mock_data import HabitItem
except ImportError:
    from theme import (
        COLOR_PRIMARY,
        COLOR_PRIMARY_HOVER,
        COLOR_PRIMARY_DARK,
        COLOR_ACCENT,
        COLOR_SUCCESS,
        COLOR_TEXT_DARK,
        COLOR_TEXT_MUTED,
        COLOR_TEXT_LIGHT,
        COLOR_CARD_BG,
        COLOR_CARD_BORDER,
        COLOR_DISABLED,
        COLOR_DISABLED_TEXT,
        COLOR_DANGER
    )
    from components import Card, Button, ProgressBar, draw_text, fit_text
    from text_input import TextInput
    from mock_data import HabitItem


class HabitScreen:
    """Màn hình quản lý habit hằng ngày và xem tiến độ hoàn thành trong ngày."""
    def __init__(
        self,
        on_complete_habit: Callable[[int], Tuple[bool, str]],
        on_create_habit: Callable[[str, str], Tuple[bool, str]],
        on_delete_habit: Callable[[int], Tuple[bool, str]],
        show_notification: Callable[[str, str], None]
    ):
        self.on_complete_habit = on_complete_habit
        self.on_create_habit = on_create_habit
        self.on_delete_habit = on_delete_habit
        self.show_notification = show_notification

        # Cột trái: card chứa danh sách habit
        self.list_card = Card((50, 90, 560, 480), title="Daily Habits", subtitle="Complete tasks to earn coins and level up your pet")

        # Cột phải: card tổng kết trong ngày
        self.summary_card = Card((630, 90, 280, 480), title="Progress", subtitle="Today's routine summary")

        # Các nút Complete được tạo động cho từng habit trong lúc render
        self.habit_buttons: dict[int, Button] = {}

        # Các nút xóa (icon thùng rác) được tạo động cho từng habit
        self.delete_buttons: dict[int, Button] = {}

        # Theo dõi các request đang xử lý để tránh click trùng
        self.in_flight_habit_id = None
        self.in_flight_create = False

        # Trạng thái dialog xác nhận xóa habit
        self.pending_delete_id = None
        self.pending_delete_title = ""
        self.in_flight_delete = False

        # Dialog xác nhận xóa (modal), dùng lại style Card/Button hiện có
        self.dialog_card = Card(
            (250, 205, 460, 230),
            title="Delete Habit",
            subtitle="This action cannot be undone."
        )
        self.dialog_cancel = Button(
            rect=(300, 365, 160, 40),
            text="Cancel",
            on_click=self._cancel_delete,
            bg_color=(240, 235, 225),
            hover_color=(230, 224, 212),
            text_color=COLOR_TEXT_DARK,
            font_size=14
        )
        self.dialog_delete = Button(
            rect=(500, 365, 160, 40),
            text="Delete",
            on_click=self._confirm_delete,
            bg_color=COLOR_DANGER,
            hover_color=(200, 88, 82),
            font_size=14
        )

        # Trạng thái cuộn cho người chơi có nhiều habit hơn mức vừa một màn hình
        self.scroll_offset = 0.0
        self._max_scroll = 0.0

        # Form tạo habit mới (cột phải, bên dưới phần tổng kết ngày)
        self.input_title = TextInput(
            rect=(650, 346, 240, 34),
            placeholder="e.g. Drink 2L of water",
            max_length=100,
            font_size=12
        )
        self.input_description = TextInput(
            rect=(650, 388, 240, 30),
            placeholder="Note (optional)",
            max_length=200,
            font_size=11
        )
        self.btn_add_habit = Button(
            rect=(650, 428, 240, 36),
            text="Add Habit",
            on_click=self._trigger_create,
            bg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            font_size=13
        )

    def on_show(self):
        """Xóa trạng thái tạm khi mở màn hình."""
        self.in_flight_habit_id = None
        self.in_flight_create = False
        self.pending_delete_id = None
        self.pending_delete_title = ""
        self.in_flight_delete = False
        self._clamp_scroll()

    def _trigger_complete(self, habit_id: int):
        if self.in_flight_habit_id is not None:
            return
        self.in_flight_habit_id = habit_id
        try:
            success, msg = self.on_complete_habit(habit_id)
            self.show_notification(msg, "success" if success else "error")
        finally:
            self.in_flight_habit_id = None

    def _trigger_create(self):
        if self.in_flight_create:
            return

        title = self.input_title.text.strip()
        if not title:
            self.show_notification("Please enter a habit title.", "error")
            return

        self.in_flight_create = True
        success, msg = self.on_create_habit(title, self.input_description.text.strip())
        self.show_notification(msg, "success" if success else "error")

        if success:
            self.input_title.clear()
            self.input_description.clear()
            self.input_title.is_focused = False
            self.input_description.is_focused = False
            self.scroll_offset = 0.0

    def _clamp_scroll(self):
        self.scroll_offset = max(0.0, min(self.scroll_offset, self._max_scroll))

    def is_modal_open(self) -> bool:
        """Cho app biết dialog xác nhận đang mở để chặn điều hướng."""
        return self.pending_delete_id is not None

    def _request_delete(self, habit_id: int, title: str):
        """Mở dialog xác nhận xóa cho đúng habit được chọn."""
        if self.in_flight_delete or self.pending_delete_id is not None:
            return
        self.pending_delete_id = habit_id
        self.pending_delete_title = title

        # Bật lại hai nút ngay khi mở dialog; nếu lần xóa trước thất bại,
        # chúng có thể vẫn đang ở trạng thái disabled từ frame "Deleting...".
        self.dialog_cancel.enabled = True
        self.dialog_delete.enabled = True
        self.dialog_delete.text = "Delete"

    def _cancel_delete(self):
        """Đóng dialog mà không thay đổi dữ liệu."""
        if self.in_flight_delete:
            return
        self.pending_delete_id = None
        self.pending_delete_title = ""
        self.show_notification("Deletion cancelled.", "info")

    def _confirm_delete(self):
        """Gọi callback xóa; giữ dialog thêm một frame để chặn click trùng."""
        if self.pending_delete_id is None or self.in_flight_delete:
            return

        self.in_flight_delete = True
        success, msg = self.on_delete_habit(self.pending_delete_id)
        self.show_notification(msg, "success" if success else "error")

    def handle_event(self, event: pygame.event.Event):
        # Khi dialog xác nhận đang mở, chỉ xử lý hai nút của dialog.
        # Điều này cũng chặn cuộn, nhập liệu và nút Complete phía sau.
        if self.pending_delete_id is not None:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self._cancel_delete()
                return
            self.dialog_cancel.handle_event(event)
            self.dialog_delete.handle_event(event)
            return

        # Cuộn danh sách habit bằng con lăn chuột khi trỏ vào vùng danh sách.
        if event.type == pygame.MOUSEWHEEL:
            if self.list_card.rect.collidepoint(pygame.mouse.get_pos()):
                self.scroll_offset -= event.y * 30
                self._clamp_scroll()
            return

        # Nhấn Enter ở một trong hai ô của form sẽ gửi habit mới.
        if self.input_title.handle_event(event):
            self._trigger_create()
            return
        if self.input_description.handle_event(event):
            self._trigger_create()
            return

        self.btn_add_habit.handle_event(event)

        for btn in self.habit_buttons.values():
            btn.handle_event(event)

        for btn in self.delete_buttons.values():
            if btn.handle_event(event):
                return

    def update(self, dt: float):
        self.input_title.update(dt)
        self.input_description.update(dt)

    def render(self, surface: pygame.Surface, habits: List[HabitItem], completed_count: int, total_count: int, progress_pct: float):
        # 1. Render cả hai card khung
        self.list_card.render(surface)
        self.summary_card.render(surface)

        viewport = pygame.Rect(60, 150, 540, 400)
        item_h = 76
        gap = 14

        # Cho phép lượt click tiếp theo tạo habit mới khi frame này đã hiển thị.
        self.in_flight_create = False

        content_height = (len(habits) * (item_h + gap) - gap) if habits else 0
        self._max_scroll = max(0.0, float(content_height - viewport.height))
        self._clamp_scroll()

        self.habit_buttons.clear()
        self.delete_buttons.clear()

        if not habits:
            empty_box = pygame.Rect(70, 200, 520, 140)
            pygame.draw.rect(surface, (250, 248, 244), empty_box, border_radius=10)
            pygame.draw.rect(surface, COLOR_CARD_BORDER, empty_box, width=1, border_radius=10)
            draw_text(surface, "No Active Habits Today", empty_box.center, font_size=17, color=COLOR_PRIMARY_DARK, bold=True, align="center")
            draw_text(surface, "Add your first habit on the right to start earning rewards!", (empty_box.centerx, empty_box.centery + 26), font_size=13, color=COLOR_TEXT_MUTED, align="center")
        else:
            previous_clip = surface.get_clip()
            surface.set_clip(viewport)

            item_y = 160 - int(self.scroll_offset)

            for habit in habits:
                # Bỏ qua các dòng nằm hoàn toàn ngoài vùng danh sách hiển thị
                if item_y + item_h >= viewport.top and item_y <= viewport.bottom:
                    # Nền card item
                    bg_col = (250, 252, 250) if habit.completed else COLOR_CARD_BG
                    border_col = (210, 230, 215) if habit.completed else COLOR_CARD_BORDER
                    item_rect = pygame.Rect(70, item_y, 520, item_h)

                    pygame.draw.rect(surface, bg_col, item_rect, border_radius=10)
                    pygame.draw.rect(surface, border_col, item_rect, width=1, border_radius=10)

                    # Icon ô đánh dấu / vòng tròn trạng thái
                    icon_center = (98, item_y + item_h // 2)
                    if habit.completed:
                        pygame.draw.circle(surface, COLOR_SUCCESS, icon_center, 14)
                        pygame.draw.lines(surface, (255, 255, 255), False, [
                            (icon_center[0] - 6, icon_center[1]),
                            (icon_center[0] - 1, icon_center[1] + 5),
                            (icon_center[0] + 6, icon_center[1] - 4)
                        ], 2)
                    else:
                        pygame.draw.circle(surface, (230, 225, 218), icon_center, 14)
                        pygame.draw.circle(surface, (190, 185, 178), icon_center, 14, width=2)

                    # Tiêu đề & mô tả (chừa chỗ cho nút xóa nhỏ bên phải)
                    title_col = COLOR_TEXT_MUTED if habit.completed else COLOR_TEXT_DARK
                    draw_text(surface, fit_text(habit.title, 16, 300, bold=True), (126, item_y + 14), font_size=16, color=title_col, bold=True)
                    desc = habit.description if habit.description else "Complete this task for daily rewards"
                    draw_text(surface, fit_text(desc, 12, 300), (126, item_y + 36), font_size=12, color=COLOR_TEXT_MUTED)

                    # Nhãn phần thưởng (giá trị do backend trả về)
                    badge_text = f"+{habit.reward_coins} Coin  +{habit.reward_exp} EXP"
                    draw_text(surface, badge_text, (126, item_y + 54), font_size=11, color=COLOR_PRIMARY, bold=True)

                    # Nút xóa nhỏ (icon thùng rác) cho từng habit
                    delete_rect = pygame.Rect(430, item_y + 24, 28, 28)
                    delete_btn = Button(
                        delete_rect,
                        "",
                        on_click=lambda h=habit.id, t=habit.title: self._request_delete(h, t),
                        enabled=not self.in_flight_delete,
                        bg_color=(252, 238, 235),
                        hover_color=(246, 218, 214),
                        border_radius=8,
                        font_size=11
                    )

                    if viewport.contains(delete_rect):
                        self.delete_buttons[habit.id] = delete_btn
                        delete_btn.render(surface)
                        self._draw_trash_icon(
                            surface,
                            delete_rect,
                            COLOR_DANGER if delete_btn.enabled else COLOR_DISABLED_TEXT
                        )

                    # Nút Complete
                    btn_rect = pygame.Rect(470, item_y + 20, 105, 36)
                    if habit.completed:
                        btn = Button(
                            btn_rect,
                            "Done",
                            enabled=False,
                            bg_color=COLOR_DISABLED,
                            text_color=COLOR_DISABLED_TEXT,
                            font_size=13
                        )
                    else:
                        hid = habit.id
                        is_loading = (self.in_flight_habit_id == hid)
                        btn = Button(
                            btn_rect,
                            "Saving..." if is_loading else "Complete",
                            on_click=lambda h=hid: self._trigger_complete(h),
                            enabled=not is_loading,
                            bg_color=COLOR_PRIMARY,
                            hover_color=COLOR_PRIMARY_HOVER,
                            font_size=13
                        )

                    # Chỉ đăng ký các nút nằm hoàn toàn trong vùng hiển thị
                    if viewport.contains(btn_rect):
                        self.habit_buttons[habit.id] = btn
                        btn.render(surface)

                item_y += item_h + gap

            surface.set_clip(previous_clip)

            # Thanh cuộn mảnh khi danh sách dài hơn vùng hiển thị
            if self._max_scroll > 0:
                track = pygame.Rect(596, 160, 6, 380)
                pygame.draw.rect(surface, (235, 230, 222), track, border_radius=3)

                visible_ratio = viewport.height / max(1.0, float(content_height))
                thumb_h = max(28, int(track.height * visible_ratio))
                travel = track.height - thumb_h
                thumb_y = track.y + int(travel * (self.scroll_offset / self._max_scroll))
                pygame.draw.rect(surface, (196, 191, 183), (track.x, thumb_y, track.width, thumb_h), border_radius=3)

        # 2. Render card phải: tổng kết tiến độ
        center_x = 770
        draw_text(surface, "Overall Completion", (center_x, 170), font_size=14, color=COLOR_TEXT_MUTED, bold=True, align="center")

        pct_str = f"{int(progress_pct)}%"
        draw_text(surface, pct_str, (center_x, 220), font_size=38, color=COLOR_PRIMARY_DARK, bold=True, align="center")
        draw_text(surface, f"{completed_count} of {total_count} tasks finished", (center_x, 260), font_size=13, color=COLOR_TEXT_MUTED, align="center")

        summary_bar = ProgressBar(
            rect=(660, 290, 220, 16),
            current_val=completed_count,
            max_val=total_count if total_count > 0 else 1,
            fill_color=COLOR_PRIMARY,
            show_numbers=False
        )
        summary_bar.render(surface)

        # 3. Form tạo habit mới
        draw_text(surface, "Add a Daily Habit", (center_x, 330), font_size=14, color=COLOR_PRIMARY_DARK, bold=True, align="center")

        self.input_title.render(surface)
        self.input_description.render(surface)

        self.btn_add_habit.text = "Adding..." if self.in_flight_create else "Add Habit"
        self.btn_add_habit.enabled = not self.in_flight_create
        self.btn_add_habit.render(surface)

        draw_text(surface, "New habits are saved to your daily routine.", (center_x, 480), font_size=11, color=COLOR_TEXT_MUTED, align="center")
        draw_text(surface, "Completing habits earns Coins and pet EXP.", (center_x, 498), font_size=11, color=COLOR_PRIMARY, bold=True, align="center")

        # Dialog xác nhận xóa (modal) phải nằm trên toàn bộ màn hình habit.
        if self.pending_delete_id is not None:
            self._render_delete_dialog(surface)

        # Đóng dialog sau frame xử lý để chặn click trùng trong cùng batch sự kiện.
        if self.in_flight_delete:
            self.in_flight_delete = False
            self.pending_delete_id = None
            self.pending_delete_title = ""

    def _draw_trash_icon(self, surface: pygame.Surface, rect: pygame.Rect, color):
        """Vẽ icon thùng rác nhỏ cho nút xóa."""
        cx, cy = rect.center

        # Nắp thùng
        pygame.draw.line(surface, color, (cx - 7, cy - 7), (cx + 7, cy - 7), 2)
        pygame.draw.line(surface, color, (cx - 3, cy - 10), (cx + 3, cy - 10), 2)

        # Thân thùng
        pygame.draw.rect(surface, color, (cx - 6, cy - 4, 12, 12), width=2, border_radius=2)

        # Hai vạch dọc trên thân thùng
        pygame.draw.line(surface, color, (cx - 2, cy - 1), (cx - 2, cy + 5), 1)
        pygame.draw.line(surface, color, (cx + 2, cy - 1), (cx + 2, cy + 5), 1)

    def _render_delete_dialog(self, surface: pygame.Surface):
        """Vẽ lớp phủ và dialog xác nhận xóa habit."""
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((30, 25, 20, 120))
        surface.blit(overlay, (0, 0))

        self.dialog_card.render(surface)
        center_x = self.dialog_card.rect.centerx

        draw_text(
            surface,
            "Are you sure you want to delete this habit?",
            (center_x, 286),
            font_size=14,
            color=COLOR_TEXT_DARK,
            bold=True,
            align="center"
        )

        title = fit_text(self.pending_delete_title, 13, 380)
        draw_text(
            surface,
            f'"{title}"',
            (center_x, 314),
            font_size=13,
            color=COLOR_TEXT_MUTED,
            align="center"
        )

        self.dialog_cancel.enabled = not self.in_flight_delete
        self.dialog_delete.enabled = not self.in_flight_delete
        self.dialog_delete.text = "Deleting..." if self.in_flight_delete else "Delete"
        self.dialog_cancel.render(surface)
        self.dialog_delete.render(surface)
