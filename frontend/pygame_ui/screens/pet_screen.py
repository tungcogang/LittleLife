"""
Pet Screen for LittleLife Pygame UI.
Displays pet avatar, name, level, exp progress bar, stats (hunger, happiness, energy, health),
and action buttons (Feed, Play, Sleep).
Also supports in-game Pet Adoption/Creation when the user does not have a pet yet.
"""
import math
import pygame
from typing import Callable, Tuple, Optional
try:
    from ..theme import (
        COLOR_BG,
        COLOR_PRIMARY,
        COLOR_PRIMARY_HOVER,
        COLOR_PRIMARY_DARK,
        COLOR_ACCENT,
        COLOR_ACCENT_HOVER,
        COLOR_HUNGER,
        COLOR_HAPPINESS,
        COLOR_ENERGY,
        COLOR_HEALTH,
        COLOR_EXP,
        COLOR_TEXT_DARK,
        COLOR_TEXT_MUTED,
        COLOR_TEXT_LIGHT,
        COLOR_CARD_BG,
        COLOR_CARD_BORDER
    )
    from ..components import Card, Button, ProgressBar, draw_text
    from ..text_input import TextInput
    from ..mock_data import PetState
except ImportError:
    from theme import (
        COLOR_BG,
        COLOR_PRIMARY,
        COLOR_PRIMARY_HOVER,
        COLOR_PRIMARY_DARK,
        COLOR_ACCENT,
        COLOR_ACCENT_HOVER,
        COLOR_HUNGER,
        COLOR_HAPPINESS,
        COLOR_ENERGY,
        COLOR_HEALTH,
        COLOR_EXP,
        COLOR_TEXT_DARK,
        COLOR_TEXT_MUTED,
        COLOR_TEXT_LIGHT,
        COLOR_CARD_BG,
        COLOR_CARD_BORDER
    )
    from components import Card, Button, ProgressBar, draw_text
    from text_input import TextInput
    from mock_data import PetState


class PetScreen:
    """The main Pet interaction screen with Pet Adoption flow."""
    def __init__(
        self,
        on_feed: Callable[[], Tuple[bool, str]],
        on_play: Callable[[], Tuple[bool, str]],
        on_sleep: Callable[[], Tuple[bool, str]],
        on_create_pet: Callable[[str], Tuple[bool, str]],
        show_notification: Callable[[str, str], None]
    ):
        self.on_feed = on_feed
        self.on_play = on_play
        self.on_sleep = on_sleep
        self.on_create_pet = on_create_pet
        self.show_notification = show_notification

        # Animation timer for cute pet idle bobbing
        self.anim_time = 0.0

        # Avatar & Profile Card
        self.avatar_card = Card((50, 90, 380, 480), title="Pet Profile", subtitle="Your faithful life companion")

        # Status & Stats Card
        self.stats_card = Card((460, 90, 450, 480), title="Vitals & Needs", subtitle="Keep stats high by completing daily goals")

        # Action Buttons
        btn_y = 500
        btn_width = 110
        btn_height = 44
        gap = 20
        start_x = 480

        self.btn_feed = Button(
            (start_x, btn_y, btn_width, btn_height),
            "Feed",
            on_click=self._handle_feed,
            bg_color=COLOR_HUNGER,
            hover_color=(235, 120, 90)
        )
        self.btn_play = Button(
            (start_x + btn_width + gap, btn_y, btn_width, btn_height),
            "Play",
            on_click=self._handle_play,
            bg_color=COLOR_HAPPINESS,
            hover_color=(240, 175, 60),
            text_color=(60, 50, 30)
        )
        self.btn_sleep = Button(
            (start_x + (btn_width + gap) * 2, btn_y, btn_width, btn_height),
            "Sleep",
            on_click=self._handle_sleep,
            bg_color=COLOR_ENERGY,
            hover_color=(105, 175, 220),
            text_color=(30, 50, 70)
        )

        # Pet Adoption Controls (when no pet exists)
        self.input_pet_name = TextInput(
            rect=(500, 260, 240, 40),
            placeholder="e.g. Mochi, Luna, Bao",
            max_length=30
        )
        self.btn_create_pet = Button(
            rect=(755, 260, 120, 40),
            text="Adopt Pet",
            on_click=self._handle_create_pet,
            bg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            font_size=14
        )

        # Action lock to avoid spamming while an action is in progress
        self.action_in_progress = False

    def _handle_feed(self):
        if self.action_in_progress:
            return
        self.action_in_progress = True
        try:
            success, msg = self.on_feed()
            self.show_notification(msg, "success" if success else "error")
        finally:
            self.action_in_progress = False

    def _handle_play(self):
        if self.action_in_progress:
            return
        self.action_in_progress = True
        try:
            success, msg = self.on_play()
            self.show_notification(msg, "success" if success else "error")
        finally:
            self.action_in_progress = False

    def _handle_sleep(self):
        if self.action_in_progress:
            return
        self.action_in_progress = True
        try:
            success, msg = self.on_sleep()
            self.show_notification(msg, "success" if success else "error")
        finally:
            self.action_in_progress = False

    def _handle_create_pet(self):
        if self.action_in_progress:
            return
        name = self.input_pet_name.text.strip()
        if not name:
            self.show_notification("Please enter a name for your pet!", "error")
            return
        self.action_in_progress = True
        try:
            success, msg = self.on_create_pet(name)
            self.show_notification(msg, "success" if success else "error")
            if success:
                self.input_pet_name.text = ""
        finally:
            self.action_in_progress = False

    def handle_event(self, event: pygame.event.Event, pet_exists: bool = True):
        if pet_exists:
            self.btn_feed.handle_event(event)
            self.btn_play.handle_event(event)
            self.btn_sleep.handle_event(event)
        else:
            if self.input_pet_name.handle_event(event):
                self._handle_create_pet()
            self.btn_create_pet.handle_event(event)

    def update(self, dt: float, pet_exists: bool = True):
        self.anim_time += dt * 3.0
        if not pet_exists:
            self.input_pet_name.update(dt)

    def _draw_pet_avatar(self, surface: pygame.Surface, pet: Optional[PetState], center_x: int, center_y: int):
        """Draws a cute, friendly procedural pet creature (no external image assets needed)."""
        bob_offset = int(math.sin(self.anim_time) * 5)
        cy = center_y + bob_offset

        # Soft shadow under pet
        shadow_rect = pygame.Rect(0, 0, 140, 30)
        shadow_rect.center = (center_x, center_y + 80)
        pygame.draw.ellipse(surface, (230, 224, 215), shadow_rect)

        # Pet body
        body_color = (255, 213, 150)
        body_rect = pygame.Rect(0, 0, 150, 130)
        body_rect.center = (center_x, cy)
        pygame.draw.ellipse(surface, body_color, body_rect)
        pygame.draw.ellipse(surface, (235, 190, 130), body_rect, width=3)

        # Cute Ears
        left_ear = [(center_x - 55, cy - 40), (center_x - 30, cy - 85), (center_x - 10, cy - 50)]
        right_ear = [(center_x + 10, cy - 50), (center_x + 30, cy - 85), (center_x + 55, cy - 40)]
        pygame.draw.polygon(surface, body_color, left_ear)
        pygame.draw.polygon(surface, body_color, right_ear)
        pygame.draw.polygon(surface, (235, 190, 130), left_ear, width=3)
        pygame.draw.polygon(surface, (235, 190, 130), right_ear, width=3)

        # Inner ears (soft pink)
        pygame.draw.polygon(surface, (255, 185, 185), [(center_x - 45, cy - 43), (center_x - 30, cy - 75), (center_x - 18, cy - 50)])
        pygame.draw.polygon(surface, (255, 185, 185), [(center_x + 18, cy - 50), (center_x + 30, cy - 75), (center_x + 45, cy - 43)])

        # Cheeks (blush)
        pygame.draw.circle(surface, (255, 180, 170), (center_x - 42, cy + 12), 12)
        pygame.draw.circle(surface, (255, 180, 170), (center_x + 42, cy + 12), 12)

        # Eyes & expressions
        eye_y = cy - 2
        energy_val = pet.energy if pet else 100
        happiness_val = pet.happiness if pet else 100

        if energy_val < 20:
            # Tired sleepy eyes (- -)
            pygame.draw.line(surface, COLOR_TEXT_DARK, (center_x - 30, eye_y), (center_x - 12, eye_y), 3)
            pygame.draw.line(surface, COLOR_TEXT_DARK, (center_x + 12, eye_y), (center_x + 30, eye_y), 3)
        elif happiness_val >= 60:
            # Joyful curved arc eyes (^ ^)
            pygame.draw.arc(surface, COLOR_TEXT_DARK, (center_x - 32, eye_y - 6, 20, 16), 0.2, 3.0, 3)
            pygame.draw.arc(surface, COLOR_TEXT_DARK, (center_x + 12, eye_y - 6, 20, 16), 0.2, 3.0, 3)
        else:
            # Normal open eyes
            pygame.draw.circle(surface, COLOR_TEXT_DARK, (center_x - 22, eye_y), 6)
            pygame.draw.circle(surface, COLOR_TEXT_DARK, (center_x + 22, eye_y), 6)
            pygame.draw.circle(surface, (255, 255, 255), (center_x - 24, eye_y - 2), 2)
            pygame.draw.circle(surface, (255, 255, 255), (center_x + 20, eye_y - 2), 2)

        # Tiny nose & mouth
        pygame.draw.polygon(surface, (210, 110, 90), [(center_x - 4, cy + 8), (center_x + 4, cy + 8), (center_x, cy + 13)])
        pygame.draw.arc(surface, COLOR_TEXT_DARK, (center_x - 10, cy + 10, 20, 12), 3.4, 6.0, 2)

        mood = "Ecstatic ✨" if happiness_val >= 80 else ("Happy 😊" if happiness_val >= 50 else "A bit lonely 🥺")
        if pet is None:
            mood = "Awaiting Adoption 🥚"
        draw_text(surface, f"Mood: {mood}", (center_x, center_y + 115), font_size=15, color=COLOR_TEXT_MUTED, bold=True, align="center")

    def render(self, surface: pygame.Surface, pet: Optional[PetState]):
        # 1. Render Left Column: Pet Profile
        self.avatar_card.render(surface)

        if pet is None:
            # No Pet Found State – Adopt Pet Interface
            draw_text(surface, "Egg Incubator", (240, 155), font_size=24, color=COLOR_PRIMARY_DARK, bold=True, align="center")
            
            tag_rect = pygame.Rect(0, 0, 130, 26)
            tag_rect.center = (240, 190)
            pygame.draw.rect(surface, (244, 241, 235), tag_rect, border_radius=13)
            draw_text(surface, "Ready for Life", tag_rect.center, font_size=13, color=COLOR_TEXT_MUTED, bold=True, align="center")

            # Draw cute procedural pet silhouette / awaiting adoption
            self._draw_pet_avatar(surface, None, 240, 310)

            draw_text(surface, "Adopt a loyal life companion to start!", (240, 495), font_size=13, color=COLOR_TEXT_MUTED, align="center")

            # 2. Render Right Column: Pet Adoption Form Card
            self.stats_card.render(surface)
            draw_text(surface, "Welcome to LittleLife!", (685, 160), font_size=22, color=COLOR_PRIMARY_DARK, bold=True, align="center")
            draw_text(surface, "You don't have a pet yet. Choose a name to begin your journey.", (685, 195), font_size=13, color=COLOR_TEXT_MUTED, align="center")
            
            draw_text(surface, "Pet Name", (500, 238), font_size=13, color=COLOR_TEXT_DARK, bold=True)
            self.input_pet_name.render(surface)
            self.btn_create_pet.render(surface)

            # Informative guide box
            info_box = pygame.Rect(500, 330, 375, 160)
            pygame.draw.rect(surface, (248, 245, 239), info_box, border_radius=8)
            pygame.draw.rect(surface, (235, 229, 220), info_box, width=1, border_radius=8)
            draw_text(surface, "🌟 Companion Benefits", (info_box.x + 16, info_box.y + 16), font_size=14, color=COLOR_PRIMARY_DARK, bold=True)
            guide_lines = [
                "• Your pet gains +20 EXP with every completed habit.",
                "• Feed (+30 Hunger), Play (+20 Joy), and Sleep (+30 Energy).",
                "• Vitals and level stay synchronized with the FastAPI backend.",
            ]
            gy = info_box.y + 45
            for gl in guide_lines:
                draw_text(surface, gl, (info_box.x + 16, gy), font_size=12, color=COLOR_TEXT_DARK)
                gy += 26
            return

        # Pet Exists – Normal Pet Screen
        draw_text(surface, pet.pet_name, (240, 155), font_size=26, color=COLOR_PRIMARY_DARK, bold=True, align="center")
        
        # Level Badge
        lvl_rect = pygame.Rect(0, 0, 90, 26)
        lvl_rect.center = (240, 190)
        pygame.draw.rect(surface, (235, 243, 238), lvl_rect, border_radius=13)
        pygame.draw.rect(surface, COLOR_PRIMARY, lvl_rect, width=1, border_radius=13)
        draw_text(surface, f"Level {pet.level}", lvl_rect.center, font_size=14, color=COLOR_PRIMARY_DARK, bold=True, align="center")

        # Procedural cute pet
        self._draw_pet_avatar(surface, pet, 240, 310)

        # EXP Progress bar inside Avatar Card
        draw_text(surface, f"EXP: {pet.exp} / {pet.exp_to_next_level}", (80, 480), font_size=13, color=COLOR_TEXT_MUTED, bold=True)
        exp_bar = ProgressBar(
            rect=(80, 502, 320, 14),
            current_val=pet.exp,
            max_val=pet.exp_to_next_level,
            fill_color=COLOR_EXP,
            show_numbers=False
        )
        exp_bar.render(surface)

        # 2. Render Right Column: Vitals Card
        self.stats_card.render(surface)

        # 4 Progress Bars for Vitals
        stat_x = 490
        stat_w = 390
        bar_h = 18

        stats = [
            ("Hunger (Satiation)", pet.hunger, 100, COLOR_HUNGER, 160),
            ("Happiness", pet.happiness, 100, COLOR_HAPPINESS, 235),
            ("Energy", pet.energy, 100, COLOR_ENERGY, 310),
            ("Health", pet.health, 100, COLOR_HEALTH, 385),
        ]

        for label, val, max_v, col, y in stats:
            pbar = ProgressBar(
                rect=(stat_x, y, stat_w, bar_h),
                current_val=val,
                max_val=max_v,
                fill_color=col,
                label=label,
                show_numbers=True
            )
            pbar.render(surface)

        # Divider line before buttons
        pygame.draw.line(surface, (235, 230, 220), (480, 475), (890, 475), 1)

        # Action Buttons
        self.btn_feed.render(surface)
        self.btn_play.render(surface)
        self.btn_sleep.render(surface)
