"""
Habit Screen for LittleLife Pygame UI.
Displays daily habit list, completion statuses, complete buttons, and daily progress summary.
Works with both live backend data (GET /habits/) and local offline simulation.
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
        COLOR_DISABLED_TEXT
    )
    from ..components import Card, Button, ProgressBar, draw_text
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
        COLOR_DISABLED_TEXT
    )
    from components import Card, Button, ProgressBar, draw_text
    from mock_data import HabitItem


class HabitScreen:
    """Screen for managing daily habits and viewing daily completion progress."""
    def __init__(
        self,
        on_complete_habit: Callable[[int], Tuple[bool, str]],
        show_notification: Callable[[str, str], None]
    ):
        self.on_complete_habit = on_complete_habit
        self.show_notification = show_notification

        # Left Column: Habit List Container Card
        self.list_card = Card((50, 90, 560, 480), title="Daily Habits", subtitle="Complete tasks to earn coins and level up your pet")

        # Right Column: Daily Summary Card
        self.summary_card = Card((630, 90, 280, 480), title="Progress", subtitle="Today's routine summary")

        # Dynamic Complete buttons created per habit during event handling/rendering
        self.habit_buttons: dict[int, Button] = {}

        # Tracking in-flight requests to avoid duplicate clicks
        self.in_flight_habit_id = None

    def _trigger_complete(self, habit_id: int):
        if self.in_flight_habit_id is not None:
            return
        self.in_flight_habit_id = habit_id
        try:
            success, msg = self.on_complete_habit(habit_id)
            self.show_notification(msg, "success" if success else "error")
        finally:
            self.in_flight_habit_id = None

    def handle_event(self, event: pygame.event.Event):
        for btn in self.habit_buttons.values():
            btn.handle_event(event)

    def update(self, dt: float):
        pass

    def render(self, surface: pygame.Surface, habits: List[HabitItem], completed_count: int, total_count: int, progress_pct: float):
        # 1. Render Left Card: Habit List
        self.list_card.render(surface)

        item_y = 160
        item_h = 76
        gap = 14

        self.habit_buttons.clear()

        if not habits:
            empty_box = pygame.Rect(70, 200, 520, 140)
            pygame.draw.rect(surface, (250, 248, 244), empty_box, border_radius=10)
            pygame.draw.rect(surface, COLOR_CARD_BORDER, empty_box, width=1, border_radius=10)
            draw_text(surface, "No Active Habits Today", empty_box.center, font_size=17, color=COLOR_PRIMARY_DARK, bold=True, align="center")
            draw_text(surface, "Add habits in the database or wait for new daily routines!", (empty_box.centerx, empty_box.centery + 26), font_size=13, color=COLOR_TEXT_MUTED, align="center")
        else:
            for habit in habits:
                # Item card background
                bg_col = (250, 252, 250) if habit.completed else COLOR_CARD_BG
                border_col = (210, 230, 215) if habit.completed else COLOR_CARD_BORDER
                item_rect = pygame.Rect(70, item_y, 520, item_h)

                pygame.draw.rect(surface, bg_col, item_rect, border_radius=10)
                pygame.draw.rect(surface, border_col, item_rect, width=1, border_radius=10)

                # Checkbox / Status Circle Icon
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

                # Title & Description
                title_col = COLOR_TEXT_MUTED if habit.completed else COLOR_TEXT_DARK
                draw_text(surface, habit.title, (126, item_y + 14), font_size=16, color=title_col, bold=True)
                desc = habit.description if habit.description else "Complete this task for daily rewards"
                draw_text(surface, desc, (126, item_y + 36), font_size=12, color=COLOR_TEXT_MUTED)

                # Reward tags badge (+10 Coin and +20 EXP as defined by backend)
                badge_text = f"+{habit.reward_coins} Coin  +{habit.reward_exp} EXP"
                draw_text(surface, badge_text, (126, item_y + 54), font_size=11, color=COLOR_PRIMARY, bold=True)

                # Complete Button
                btn_rect = pygame.Rect(470, item_y + 20, 105, 36)
                if habit.completed:
                    btn = Button(
                        btn_rect,
                        "Done ✓",
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

                self.habit_buttons[habit.id] = btn
                btn.render(surface)

                item_y += item_h + gap

        # 2. Render Right Card: Progress Summary
        self.summary_card.render(surface)

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

        note_rect = pygame.Rect(650, 340, 240, 180)
        pygame.draw.rect(surface, (246, 243, 235), note_rect, border_radius=8)
        pygame.draw.rect(surface, (235, 230, 220), note_rect, width=1, border_radius=8)

        draw_text(surface, "Pet Habit Advice", (665, 355), font_size=14, color=COLOR_PRIMARY_DARK, bold=True)
        tips = [
            "• Every completed habit",
            "  rewards +10 Coins.",
            "• Your pet gains +20 EXP",
            "  and levels up over time!",
            "• Consistency keeps your",
            "  pet active and joyful."
        ]
        tip_y = 385
        for tip in tips:
            draw_text(surface, tip, (665, tip_y), font_size=12, color=COLOR_TEXT_DARK)
            tip_y += 20
