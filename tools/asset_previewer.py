"""
Công cụ xem trước asset Pygame độc lập cho LittleLife.
Kiểm tra, xem trước và xác thực toàn bộ asset của game trong assets_pack/.
Có nền caro thể hiện vùng trong suốt, zoom theo tỉ lệ, điều hướng bằng phím mũi tên,
và một chế độ So sánh Sprite Pet 5 trạng thái riêng.
"""
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pygame

# Cấu hình & màu chủ đề (bảng màu Cozy LittleLife)
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 680
FPS = 60
TITLE = "LittleLife - Asset Previewer & Validator"

COLOR_BG = (248, 245, 237)          # Kem ấm
COLOR_SIDEBAR_BG = (240, 234, 222)  # Cát nhạt
COLOR_CARD_BG = (255, 255, 255)     # Thẻ trắng sạch
COLOR_CARD_BORDER = (226, 218, 206) # Viền dịu
COLOR_PRIMARY = (118, 171, 143)     # Xanh xô thơm
COLOR_PRIMARY_DARK = (72, 120, 95)
COLOR_ACCENT = (244, 162, 97)       # Cam san hô
COLOR_TEXT_DARK = (58, 54, 50)      # Xám than
COLOR_TEXT_MUTED = (130, 125, 118)  # Xám đá nhẹ
COLOR_TEXT_LIGHT = (255, 255, 255)
COLOR_ERROR_BG = (254, 226, 226)
COLOR_ERROR_BORDER = (239, 68, 68)
COLOR_ERROR_TEXT = (185, 28, 28)

# Các danh mục được hỗ trợ, ánh xạ tới thư mục tương đối trong assets_pack
CATEGORY_DIRS = [
    ("icons/stats", "icons/stats", "Stats & Vitals"),
    ("icons/items", "icons/items", "Shop & Bag Items"),
    ("icons/ui", "icons/ui", "UI & Badges"),
    ("sprites/pet", "sprites/pet", "Pet Sprites"),
]

SCALE_LEVELS = [1.0, 2.0, 3.0, 4.0, 6.0, 8.0]


class AssetEntry:
    """Đại diện một asset kèm surface Pygame đã tải hoặc lỗi khi tải."""
    def __init__(self, category: str, path: Path):
        self.category = category
        self.path = path
        self.filename = path.name
        self.relative_path = path.as_posix()
        self.surface: Optional[pygame.Surface] = None
        self.width: int = 0
        self.height: int = 0
        self.error: Optional[str] = None
        self.has_alpha: bool = False

        self.load()

    def load(self):
        try:
            if not self.path.exists():
                self.error = f"File not found: {self.path}"
                return
            surf = pygame.image.load(str(self.path))
            self.surface = surf.convert_alpha()
            self.width, self.height = surf.get_size()
            self.has_alpha = (surf.get_flags() & pygame.SRCALPHA) or surf.get_bytesize() == 4
        except Exception as e:
            self.error = f"Failed to load image: {str(e)}"


class AssetPreviewerApp:
    """Ứng dụng Asset Previewer trung tâm."""
    def __init__(self, assets_dir: Path):
        pygame.init()
        pygame.display.set_caption(TITLE)
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True

        self.assets_dir = assets_dir
        self.categories: List[str] = [cat[0] for cat in CATEGORY_DIRS]
        self.category_titles: Dict[str, str] = {cat[0]: cat[2] for cat in CATEGORY_DIRS}
        self.assets_by_category: Dict[str, List[AssetEntry]] = {cat: [] for cat in self.categories}

        # Chế độ ứng dụng: "browse" hoặc "comparison"
        self.mode = "browse"
        self.current_category_idx = 0
        self.current_asset_idx = 0
        self.scale_idx = 2  # mặc định zoom 3.0x
        self.show_grid = True

        # Tạo sẵn surface họa tiết caro
        self._cached_checker: Optional[pygame.Surface] = None

        self._load_all_assets()

    def _load_all_assets(self):
        """Quét assets_pack và tải toàn bộ mục."""
        for cat_key, sub_dir, _ in CATEGORY_DIRS:
            target_path = self.assets_dir / sub_dir
            if target_path.exists():
                png_files = sorted(list(target_path.glob("*.png")), key=lambda p: p.name)
                for f in png_files:
                    entry = AssetEntry(cat_key, f)
                    self.assets_by_category[cat_key].append(entry)

    def current_category(self) -> str:
        return self.categories[self.current_category_idx]

    def current_asset_list(self) -> List[AssetEntry]:
        return self.assets_by_category.get(self.current_category(), [])

    def current_asset(self) -> Optional[AssetEntry]:
        items = self.current_asset_list()
        if not items:
            return None
        self.current_asset_idx = max(0, min(self.current_asset_idx, len(items) - 1))
        return items[self.current_asset_idx]

    def current_scale(self) -> float:
        return SCALE_LEVELS[self.scale_idx]

    def next_asset(self):
        items = self.current_asset_list()
        if items:
            self.current_asset_idx = (self.current_asset_idx + 1) % len(items)

    def prev_asset(self):
        items = self.current_asset_list()
        if items:
            self.current_asset_idx = (self.current_asset_idx - 1) % len(items)

    def next_category(self):
        self.current_category_idx = (self.current_category_idx + 1) % len(self.categories)
        self.current_asset_idx = 0

    def prev_category(self):
        self.current_category_idx = (self.current_category_idx - 1) % len(self.categories)
        self.current_asset_idx = 0

    def zoom_in(self):
        if self.scale_idx < len(SCALE_LEVELS) - 1:
            self.scale_idx += 1

    def zoom_out(self):
        if self.scale_idx > 0:
            self.scale_idx -= 1

    def draw_text(self, text: str, pos: Tuple[int, int], size: int = 16, color: Tuple[int, int, int] = COLOR_TEXT_DARK, bold: bool = False, align: str = "topleft") -> pygame.Rect:
        font = pygame.font.SysFont("segoeui,arial,helvetica", size, bold=bold)
        surf = font.render(str(text), True, color)
        rect = surf.get_rect()
        setattr(rect, align, pos)
        self.screen.blit(surf, rect)
        return rect

    def get_checkerboard(self, width: int, height: int, cell_size: int = 12) -> pygame.Surface:
        """Vẽ họa tiết caro kinh điển để lộ vùng trong suốt alpha."""
        surf = pygame.Surface((width, height))
        c1 = (245, 245, 245)
        c2 = (220, 220, 220)
        surf.fill(c1)
        for y in range(0, height, cell_size):
            for x in range(0, width, cell_size):
                if ((x // cell_size) + (y // cell_size)) % 2 == 1:
                    pygame.draw.rect(surf, c2, (x, y, cell_size, cell_size))
        return surf

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                    return
                # Tab hoặc P để bật/tắt chế độ so sánh pet
                elif event.key == pygame.K_TAB or event.key == pygame.K_p:
                    self.mode = "comparison" if self.mode == "browse" else "browse"
                # Điều hướng bằng phím mũi tên
                elif event.key == pygame.K_RIGHT:
                    self.next_asset()
                elif event.key == pygame.K_LEFT:
                    self.prev_asset()
                elif event.key == pygame.K_DOWN:
                    self.next_category()
                elif event.key == pygame.K_UP:
                    self.prev_category()
                # Điều khiển zoom: +/= và -
                elif event.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                    self.zoom_in()
                elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    self.zoom_out()
                # Phím số 1 - 4 để chuyển nhanh danh mục
                elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
                    idx = event.key - pygame.K_1
                    if idx < len(self.categories):
                        self.mode = "browse"
                        self.current_category_idx = idx
                        self.current_asset_idx = 0
                # G để bật/tắt lưới caro
                elif event.key == pygame.K_g:
                    self.show_grid = not self.show_grid

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    # Nhấp chuột vào tab danh mục ở thanh bên
                    mx, my = event.pos
                    # Kiểm tra nhấp chuột vào danh mục ở thanh bên
                    for i in range(len(self.categories)):
                        tab_rect = pygame.Rect(20, 110 + i * 44, 240, 36)
                        if tab_rect.collidepoint((mx, my)):
                            self.mode = "browse"
                            self.current_category_idx = i
                            self.current_asset_idx = 0
                            break
                    # Nút tab so sánh
                    comp_rect = pygame.Rect(20, 110 + len(self.categories) * 44 + 10, 240, 36)
                    if comp_rect.collidepoint((mx, my)):
                        self.mode = "comparison"

                    # Nút zoom in/out
                    zoom_in_rect = pygame.Rect(910, 22, 34, 30)
                    zoom_out_rect = pygame.Rect(870, 22, 34, 30)
                    if zoom_in_rect.collidepoint((mx, my)):
                        self.zoom_in()
                    elif zoom_out_rect.collidepoint((mx, my)):
                        self.zoom_out()

    def render_sidebar(self):
        # Nền thanh bên
        sidebar_rect = pygame.Rect(0, 0, 280, WINDOW_HEIGHT)
        pygame.draw.rect(self.screen, COLOR_SIDEBAR_BG, sidebar_rect)
        pygame.draw.line(self.screen, COLOR_CARD_BORDER, (280, 0), (280, WINDOW_HEIGHT), 1)

        # Tiêu đề đầu trang
        self.draw_text("LittleLife", (25, 24), size=22, color=COLOR_PRIMARY_DARK, bold=True)
        self.draw_text("Asset Previewer", (25, 52), size=13, color=COLOR_TEXT_MUTED, bold=True)
        pygame.draw.line(self.screen, (225, 218, 206), (25, 80), (255, 80), 1)

        # Các tab danh mục
        self.draw_text("CATEGORIES", (25, 92), size=11, color=COLOR_TEXT_MUTED, bold=True)

        for i, cat_key in enumerate(self.categories):
            count = len(self.assets_by_category.get(cat_key, []))
            is_active = (self.mode == "browse" and i == self.current_category_idx)
            tab_rect = pygame.Rect(20, 110 + i * 44, 240, 36)

            bg_col = COLOR_PRIMARY if is_active else (248, 244, 237)
            text_col = COLOR_TEXT_LIGHT if is_active else COLOR_TEXT_DARK

            pygame.draw.rect(self.screen, bg_col, tab_rect, border_radius=8)
            if not is_active:
                pygame.draw.rect(self.screen, COLOR_CARD_BORDER, tab_rect, width=1, border_radius=8)

            title = self.category_titles[cat_key]
            self.draw_text(f"{i + 1}. {title}", (tab_rect.x + 12, tab_rect.y + 9), size=13, color=text_col, bold=is_active)
            self.draw_text(f"({count})", (tab_rect.right - 12, tab_rect.y + 9), size=12, color=text_col, align="topright")

        # Tab xem so sánh riêng
        comp_y = 110 + len(self.categories) * 44 + 10
        is_comp = (self.mode == "comparison")
        comp_rect = pygame.Rect(20, comp_y, 240, 36)
        bg_col = COLOR_ACCENT if is_comp else (248, 244, 237)
        text_col = COLOR_TEXT_LIGHT if is_comp else COLOR_TEXT_DARK

        pygame.draw.rect(self.screen, bg_col, comp_rect, border_radius=8)
        if not is_comp:
            pygame.draw.rect(self.screen, COLOR_CARD_BORDER, comp_rect, width=1, border_radius=8)
        self.draw_text("🐾 Pet 5-State Comparison", (comp_rect.x + 12, comp_rect.y + 9), size=13, color=text_col, bold=is_comp)

        # Số lượng asset trong danh sách danh mục
        if self.mode == "browse":
            items = self.current_asset_list()
            self.draw_text("CATEGORY ITEMS", (25, comp_y + 60), size=11, color=COLOR_TEXT_MUTED, bold=True)
            list_box = pygame.Rect(20, comp_y + 80, 240, 170)
            pygame.draw.rect(self.screen, COLOR_CARD_BG, list_box, border_radius=8)
            pygame.draw.rect(self.screen, COLOR_CARD_BORDER, list_box, width=1, border_radius=8)

            start_idx = max(0, min(self.current_asset_idx - 2, max(0, len(items) - 6)))
            visible_items = items[start_idx:start_idx + 6]
            y_offset = list_box.y + 8
            for idx_offset, item in enumerate(visible_items):
                actual_idx = start_idx + idx_offset
                is_selected = (actual_idx == self.current_asset_idx)
                row_rect = pygame.Rect(list_box.x + 4, y_offset, list_box.width - 8, 24)
                if is_selected:
                    pygame.draw.rect(self.screen, (235, 244, 238), row_rect, border_radius=4)
                    pygame.draw.rect(self.screen, COLOR_PRIMARY, row_rect, width=1, border_radius=4)

                prefix = "▶ " if is_selected else "  "
                row_col = COLOR_PRIMARY_DARK if is_selected else COLOR_TEXT_DARK
                self.draw_text(f"{prefix}{item.filename}", (row_rect.x + 4, row_rect.y + 4), size=11, color=row_col, bold=is_selected)
                y_offset += 26

        # Khung điều khiển & tóm tắt phím tắt ở cuối thanh bên
        help_box = pygame.Rect(20, WINDOW_HEIGHT - 120, 240, 105)
        pygame.draw.rect(self.screen, (246, 241, 233), help_box, border_radius=8)
        pygame.draw.rect(self.screen, (230, 222, 212), help_box, width=1, border_radius=8)
        self.draw_text("KEYBOARD SHORTCUTS", (help_box.x + 10, help_box.y + 8), size=11, color=COLOR_TEXT_MUTED, bold=True)
        self.draw_text("◀ / ▶ : Next/Prev Asset", (help_box.x + 10, help_box.y + 26), size=11, color=COLOR_TEXT_DARK)
        self.draw_text("▲ / ▼ : Switch Category", (help_box.x + 10, help_box.y + 44), size=11, color=COLOR_TEXT_DARK)
        self.draw_text("+ / - : Zoom In / Out", (help_box.x + 10, help_box.y + 62), size=11, color=COLOR_TEXT_DARK)
        self.draw_text("TAB / P : Pet Compare | G : Grid", (help_box.x + 10, help_box.y + 80), size=11, color=COLOR_TEXT_DARK)

    def render_top_bar(self):
        header_rect = pygame.Rect(280, 0, WINDOW_WIDTH - 280, 70)
        pygame.draw.rect(self.screen, (252, 250, 246), header_rect)
        pygame.draw.line(self.screen, COLOR_CARD_BORDER, (280, 70), (WINDOW_WIDTH, 70), 1)

        if self.mode == "browse":
            cat_name = self.category_titles[self.current_category()]
            asset = self.current_asset()
            items = self.current_asset_list()
            count_str = f"Asset {self.current_asset_idx + 1} of {len(items)}" if items else "No items"
            self.draw_text(f"{cat_name}  •  {count_str}", (310, 24), size=18, color=COLOR_TEXT_DARK, bold=True)
        else:
            self.draw_text("Pet Sprites Comparison  •  5 States", (310, 24), size=18, color=COLOR_ACCENT, bold=True)

        # Điều khiển zoom ở góc trên bên phải
        scale_val = self.current_scale()
        self.draw_text(f"Zoom: {int(scale_val)}x" if scale_val.is_integer() else f"Zoom: {scale_val}x", (810, 28), size=13, color=COLOR_TEXT_MUTED, bold=True)

        zoom_out_rect = pygame.Rect(870, 22, 34, 30)
        zoom_in_rect = pygame.Rect(910, 22, 34, 30)
        for r, lbl in [(zoom_out_rect, "-"), (zoom_in_rect, "+")]:
            pygame.draw.rect(self.screen, (244, 240, 232), r, border_radius=6)
            pygame.draw.rect(self.screen, COLOR_CARD_BORDER, r, width=1, border_radius=6)
            self.draw_text(lbl, r.center, size=16, color=COLOR_TEXT_DARK, bold=True, align="center")

    def render_browse_view(self):
        asset = self.current_asset()
        main_area = pygame.Rect(310, 95, WINDOW_WIDTH - 340, WINDOW_HEIGHT - 120)

        # Khung thẻ chính
        pygame.draw.rect(self.screen, COLOR_CARD_BG, main_area, border_radius=12)
        pygame.draw.rect(self.screen, COLOR_CARD_BORDER, main_area, width=1, border_radius=12)

        if not asset:
            self.draw_text("No assets found in this category.", main_area.center, size=16, color=COLOR_TEXT_MUTED, align="center")
            return

        # Xử lý trạng thái lỗi (ảnh hỏng hoặc thiếu)
        if asset.error:
            err_box = pygame.Rect(main_area.x + 30, main_area.y + 30, main_area.width - 60, 100)
            pygame.draw.rect(self.screen, COLOR_ERROR_BG, err_box, border_radius=8)
            pygame.draw.rect(self.screen, COLOR_ERROR_BORDER, err_box, width=1, border_radius=8)
            self.draw_text("⚠ Asset Loading Error", (err_box.x + 16, err_box.y + 16), size=16, color=COLOR_ERROR_TEXT, bold=True)
            self.draw_text(asset.error, (err_box.x + 16, err_box.y + 44), size=13, color=COLOR_ERROR_TEXT)
            return

        # Vùng hiển thị viewport với họa tiết caro
        scale = self.current_scale()
        vp_width, vp_height = 400, 360
        vp_x = main_area.x + 30
        vp_y = main_area.y + 30
        vp_rect = pygame.Rect(vp_x, vp_y, vp_width, vp_height)

        # Nền caro để thấy rõ kênh alpha
        if self.show_grid:
            checker = self.get_checkerboard(vp_width, vp_height, cell_size=16)
            self.screen.blit(checker, (vp_x, vp_y))
        else:
            pygame.draw.rect(self.screen, (240, 240, 240), vp_rect)

        pygame.draw.rect(self.screen, (210, 204, 194), vp_rect, width=1, border_radius=4)

        # Phóng theo tỉ lệ rồi vẽ ảnh
        scaled_w = int(asset.width * scale)
        scaled_h = int(asset.height * scale)
        scaled_surf = pygame.transform.scale(asset.surface, (scaled_w, scaled_h))

        img_rect = scaled_surf.get_rect()
        img_rect.center = vp_rect.center
        self.screen.blit(scaled_surf, img_rect)

        # Bảng thông tin asset (cột phải của thẻ)
        meta_x = vp_rect.right + 30
        meta_y = vp_rect.y

        self.draw_text(asset.filename, (meta_x, meta_y), size=20, color=COLOR_PRIMARY_DARK, bold=True)
        self.draw_text(f"Category: {asset.category}", (meta_x, meta_y + 34), size=13, color=COLOR_TEXT_MUTED)

        # Các nhãn thông tin
        specs = [
            ("Original Size", f"{asset.width} x {asset.height} px"),
            ("Preview Size", f"{scaled_w} x {scaled_h} px ({int(scale)}x)"),
            ("Alpha Channel", "32-bit RGBA (Transparent)" if asset.has_alpha else "24-bit RGB (Opaque)"),
            ("File Format", "PNG (Lossless)"),
            ("Disk Path", str(asset.path.relative_to(self.assets_dir.parent))),
        ]

        spec_y = meta_y + 70
        for label, val in specs:
            spec_rect = pygame.Rect(meta_x, spec_y, main_area.right - meta_x - 30, 44)
            pygame.draw.rect(self.screen, (248, 245, 239), spec_rect, border_radius=6)
            pygame.draw.rect(self.screen, (235, 229, 220), spec_rect, width=1, border_radius=6)

            self.draw_text(label, (spec_rect.x + 12, spec_rect.y + 6), size=11, color=COLOR_TEXT_MUTED, bold=True)
            self.draw_text(val, (spec_rect.x + 12, spec_rect.y + 22), size=13, color=COLOR_TEXT_DARK, bold=True)
            spec_y += 50

        # Dải thumbnail chuyển nhanh ở dưới
        items = self.current_asset_list()
        thumb_bar_y = main_area.bottom - 95
        pygame.draw.line(self.screen, (235, 230, 220), (main_area.x + 20, thumb_bar_y), (main_area.right - 20, thumb_bar_y), 1)

        self.draw_text("Quick Switch (click or use Arrow Keys):", (main_area.x + 30, thumb_bar_y + 8), size=11, color=COLOR_TEXT_MUTED, bold=True)

        thumb_x = main_area.x + 30
        thumb_y = thumb_bar_y + 28
        for idx, itm in enumerate(items):
            t_box = pygame.Rect(thumb_x, thumb_y, 48, 48)
            is_cur = (idx == self.current_asset_idx)
            bg = (235, 244, 238) if is_cur else (248, 245, 239)
            border = COLOR_PRIMARY if is_cur else COLOR_CARD_BORDER

            pygame.draw.rect(self.screen, bg, t_box, border_radius=6)
            pygame.draw.rect(self.screen, border, t_box, width=2 if is_cur else 1, border_radius=6)

            if itm.surface:
                # Phóng thumbnail cho vừa khung 36x36
                fit_w = min(36, itm.width)
                fit_h = min(36, itm.height)
                t_surf = pygame.transform.smoothscale(itm.surface, (fit_w, fit_h))
                t_rect = t_surf.get_rect()
                t_rect.center = t_box.center
                self.screen.blit(t_surf, t_rect)

            thumb_x += 56
            if thumb_x + 48 > main_area.right - 30:
                break

    def render_comparison_view(self):
        """Chế độ xem riêng, đặt cạnh nhau 5 trạng thái sprite của pet."""
        main_area = pygame.Rect(310, 95, WINDOW_WIDTH - 340, WINDOW_HEIGHT - 120)
        pygame.draw.rect(self.screen, COLOR_CARD_BG, main_area, border_radius=12)
        pygame.draw.rect(self.screen, COLOR_CARD_BORDER, main_area, width=1, border_radius=12)

        self.draw_text("Pet Character Animation States (64x64 px)", (main_area.x + 30, main_area.y + 20), size=18, color=COLOR_PRIMARY_DARK, bold=True)
        self.draw_text("Visual state consistency check across all 5 primary pet moods & actions", (main_area.x + 30, main_area.y + 46), size=13, color=COLOR_TEXT_MUTED)

        pet_states = [
            ("idle", "pet_idle.png", "Idle State", "Neutral alert pose"),
            ("happy", "pet_happy.png", "Happy State", "High happiness / reward"),
            ("sad", "pet_sad.png", "Sad State", "Low hunger or energy"),
            ("eating", "pet_eating.png", "Eating State", "Triggered by feed button"),
            ("sleeping", "pet_sleeping.png", "Sleeping State", "Energy rest mode"),
        ]

        card_w = 114
        card_h = 360
        gap = 14
        start_x = main_area.x + 22
        start_y = main_area.y + 80

        scale = 1.5  # 64x64 phóng thành 96x96

        for i, (state_key, filename, label, subtitle) in enumerate(pet_states):
            x = start_x + i * (card_w + gap)
            card_rect = pygame.Rect(x, start_y, card_w, card_h)

            pygame.draw.rect(self.screen, (252, 251, 248), card_rect, border_radius=10)
            pygame.draw.rect(self.screen, COLOR_CARD_BORDER, card_rect, width=1, border_radius=10)

            # Nhãn tên trạng thái
            badge_rect = pygame.Rect(x + 8, start_y + 12, card_w - 16, 26)
            pygame.draw.rect(self.screen, (235, 243, 238), badge_rect, border_radius=6)
            self.draw_text(label, badge_rect.center, size=12, color=COLOR_PRIMARY_DARK, bold=True, align="center")

            # Khung hiển thị caro cho sprite
            box_rect = pygame.Rect(x + 9, start_y + 48, 96, 120)
            checker = self.get_checkerboard(box_rect.width, box_rect.height, cell_size=12)
            self.screen.blit(checker, box_rect.topleft)
            pygame.draw.rect(self.screen, (215, 208, 198), box_rect, width=1, border_radius=4)

            # Tìm asset pet tương ứng
            target_entry = next((e for e in self.assets_by_category.get("sprites/pet", []) if e.filename == filename), None)
            if target_entry and target_entry.surface:
                s_surf = pygame.transform.smoothscale(target_entry.surface, (96, 96))
                s_rect = s_surf.get_rect()
                s_rect.center = box_rect.center
                self.screen.blit(s_surf, s_rect)
            else:
                self.draw_text("Missing", box_rect.center, size=12, color=COLOR_ERROR_TEXT, bold=True, align="center")

            # Ghi chú mô tả trạng thái
            self.draw_text(filename, (x + 8, start_y + 180), size=11, color=COLOR_TEXT_MUTED, bold=True)
            self.draw_text(subtitle, (x + 8, start_y + 204), size=11, color=COLOR_TEXT_DARK)

            # Nhãn xác thực trạng thái
            valid_rect = pygame.Rect(x + 8, card_rect.bottom - 36, card_w - 16, 24)
            if target_entry and not target_entry.error:
                pygame.draw.rect(self.screen, (220, 245, 225), valid_rect, border_radius=4)
                self.draw_text("✓ Verified", valid_rect.center, size=11, color=(45, 90, 55), bold=True, align="center")
            else:
                pygame.draw.rect(self.screen, COLOR_ERROR_BG, valid_rect, border_radius=4)
                self.draw_text("✕ Error", valid_rect.center, size=11, color=COLOR_ERROR_TEXT, bold=True, align="center")

    def render(self):
        self.screen.fill(COLOR_BG)
        self.render_sidebar()
        self.render_top_bar()

        if self.mode == "browse":
            self.render_browse_view()
        else:
            self.render_comparison_view()

        pygame.display.flip()

    def run(self):
        while self.running:
            self.handle_events()
            self.render()
            self.clock.tick(FPS)
        pygame.quit()


def main():
    # Xác định đường dẫn assets_pack tương đối so với gốc repo
    base_dir = Path(__file__).resolve().parent.parent
    assets_dir = base_dir / "assets_pack"

    app = AssetPreviewerApp(assets_dir)
    app.run()


if __name__ == "__main__":
    main()
