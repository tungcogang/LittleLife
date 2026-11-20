
import pygame
import sys

# 1. Khởi tạo Pygame
pygame.init()

# 2. Thiết lập kích thước cửa sổ
WIDTH = 1000
HEIGHT = 600

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("LittleLife - A Little Life with Pets")

# 3. Thiết lập màu sắc
WHITE = (255, 255, 255)
BLACK = (30, 30, 30)

# 4. Khởi tạo font chữ
font = pygame.font.SysFont("Arial", 48)

# 5. Vòng lặp chính của game
running = True

while running:

    # Xử lý sự kiện
    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

    # Vẽ giao diện
    screen.fill(WHITE)

    title = font.render("Welcome to LittleLife!", True, BLACK)

    screen.blit(
        title,
        (WIDTH // 2 - title.get_width() // 2, HEIGHT // 2)
    )

    # Cập nhật màn hình
    pygame.display.flip()

# 6. Kết thúc chương trình
pygame.quit()
sys.exit()
