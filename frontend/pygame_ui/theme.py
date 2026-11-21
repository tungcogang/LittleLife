"""
Cấu hình theme cho LittleLife Pygame UI.
Bao gồm bảng màu dễ chịu, cấu hình font và các hằng số kích thước.
"""
import pygame

# Cấu hình cửa sổ
WINDOW_WIDTH = 960
WINDOW_HEIGHT = 640
FPS = 60
TITLE = "LittleLife - Cozy Virtual Pet & Daily Habit Companion"

# Bảng màu pastel & đất ấm dễ chịu
COLOR_BG = (248, 245, 237)          # Kem ấm
COLOR_CARD_BG = (255, 255, 255)     # Card trắng sạch
COLOR_CARD_BORDER = (230, 222, 210) # Viền cát dịu
COLOR_NAV_BG = (238, 230, 217)      # Nền thanh điều hướng

# Màu chính & màu nhấn
COLOR_PRIMARY = (118, 171, 143)     # Xanh xô thơm (thân thiện & dịu mắt)
COLOR_PRIMARY_HOVER = (98, 151, 123)
COLOR_PRIMARY_DARK = (72, 120, 95)

COLOR_ACCENT = (244, 162, 97)       # San hô ấm / cam pastel
COLOR_ACCENT_HOVER = (231, 142, 75)

COLOR_COIN = (234, 179, 8)          # Hổ phách vàng
COLOR_COIN_BG = (254, 243, 199)     # Nền viên hổ phách dịu
COLOR_COIN_BORDER = (252, 211, 77)

# Màu thanh trạng thái
COLOR_HUNGER = (240, 140, 110)      # Hồng đào
COLOR_HAPPINESS = (250, 190, 88)    # Vàng nắng
COLOR_ENERGY = (130, 195, 236)      # Xanh da trời
COLOR_HEALTH = (120, 205, 140)      # Xanh bạc hà tươi
COLOR_EXP = (175, 145, 225)         # Oải hương dịu

# Màu chữ
COLOR_TEXT_DARK = (58, 54, 50)      # Nâu than ấm (dễ đọc)
COLOR_TEXT_MUTED = (130, 125, 118)  # Xám đá dịu
COLOR_TEXT_LIGHT = (255, 255, 255)  # Chữ trắng

# Màu trạng thái
COLOR_SUCCESS = (118, 171, 143)
COLOR_DANGER = (225, 112, 105)
COLOR_DISABLED = (205, 200, 195)
COLOR_DISABLED_TEXT = (150, 145, 140)

_fonts = {}

def get_font(size: int = 18, bold: bool = False) -> pygame.font.Font:
    """Hàm phụ nạp muộn và cache font hệ thống."""
    if not pygame.font.get_init():
        pygame.font.init()
    
    key = (size, bold)
    if key not in _fonts:
        # Thử tìm font bo tròn thân thiện như Segoe UI, Arial; nếu không có thì dùng SysFont
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
