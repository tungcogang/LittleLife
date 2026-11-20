"""
Theme configuration for LittleLife Pygame UI.
Contains cozy color palette, font configurations, and dimension constants.
"""
import pygame

# Window settings
WINDOW_WIDTH = 960
WINDOW_HEIGHT = 640
FPS = 60
TITLE = "LittleLife - Cozy Virtual Pet & Daily Habit Companion"

# Cozy Pastel & Warm Earth Color Palette
COLOR_BG = (248, 245, 237)          # Warm cream
COLOR_CARD_BG = (255, 255, 255)     # Clean white card
COLOR_CARD_BORDER = (230, 222, 210) # Soft sand border
COLOR_NAV_BG = (238, 230, 217)      # Navigation bar background

# Primary & Accent colors
COLOR_PRIMARY = (118, 171, 143)     # Sage green (friendly & soothing)
COLOR_PRIMARY_HOVER = (98, 151, 123)
COLOR_PRIMARY_DARK = (72, 120, 95)

COLOR_ACCENT = (244, 162, 97)       # Warm coral / pastel orange
COLOR_ACCENT_HOVER = (231, 142, 75)

COLOR_COIN = (234, 179, 8)          # Golden amber
COLOR_COIN_BG = (254, 243, 199)     # Soft amber pill background
COLOR_COIN_BORDER = (252, 211, 77)

# Status bar colors
COLOR_HUNGER = (240, 140, 110)      # Salmon peach
COLOR_HAPPINESS = (250, 190, 88)    # Sunny yellow
COLOR_ENERGY = (130, 195, 236)      # Sky blue
COLOR_HEALTH = (120, 205, 140)      # Fresh mint green
COLOR_EXP = (175, 145, 225)         # Gentle lavender

# Text colors
COLOR_TEXT_DARK = (58, 54, 50)      # Charcoal warm brown (high readability)
COLOR_TEXT_MUTED = (130, 125, 118)  # Gentle stone grey
COLOR_TEXT_LIGHT = (255, 255, 255)  # White text

# State colors
COLOR_SUCCESS = (118, 171, 143)
COLOR_DANGER = (225, 112, 105)
COLOR_DISABLED = (205, 200, 195)
COLOR_DISABLED_TEXT = (150, 145, 140)

_fonts = {}

def get_font(size: int = 18, bold: bool = False) -> pygame.font.Font:
    """Helper to lazily load and cache system fonts."""
    if not pygame.font.get_init():
        pygame.font.init()
    
    key = (size, bold)
    if key not in _fonts:
        # Try finding a friendly rounded font like Segoe UI, Arial, or fallback to SysFont
        font_names = ["segoeui", "helvetica", "arial", "dejavusans"]
        matched_font = None
        for name in font_names:
            matched_font = pygame.font.match_font(name, bold=bold)
            if matched_font:
                try:
                    _fonts[key] = pygame.font.Font(matched_font, size)
                    break
                except Exception:
                    matched_font = None
        if key not in _fonts:
            _fonts[key] = pygame.font.SysFont(None, size, bold=bold)
            
    return _fonts[key]
