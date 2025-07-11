import pygame
import sys
import random
import os

# Constants
SCREEN_WIDTH = 900
SCREEN_HEIGHT = 700
PADDLE_WIDTH = 200
PADDLE_HEIGHT = 15
BALL_RADIUS = 10
BRICK_WIDTH = 70
BRICK_HEIGHT = 20

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)

# Init
pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Arkanoid Enhanced")
clock = pygame.time.Clock()

# Game States
GAME_STATE_TITLE = 0
GAME_STATE_PLAYING = 1
GAME_STATE_GAME_OVER = 2

current_game_state = GAME_STATE_TITLE
player_lives = 3
player_score = 0
current_level_num = 0
is_muted = False

# Load sound safely
try:
    bounce_sound = pygame.mixer.Sound("assets/bounce.wav")
except pygame.error:
    bounce_sound = None
    print("Warning: bounce.wav not found")

# Fonts
font_path = os.path.join("fonts", "PressStart2P-Regular.ttf")

font_large = pygame.font.Font(font_path, 40)
font_medium = pygame.font.Font(font_path, 24)
font_small = pygame.font.Font(font_path, 16)

# Classes
class Paddle(pygame.Rect):
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height)
        self.speed = 14
        self.original_width = width

    def move(self, direction):
        self.x += direction * self.speed
        if self.left < 0:
            self.left = 0
        if self.right > SCREEN_WIDTH:
            self.right = SCREEN_WIDTH

    def resize(self, new_width):
        self.width = new_width
        self.x = self.centerx - (new_width / 2)

class Ball(pygame.Rect):
    def __init__(self, x, y, radius):
        super().__init__(x - radius, y - radius, radius * 2, radius * 2)
        self.dx = 5
        self.dy = -5
        self.original_speed_x = 5
        self.original_speed_y = -5
        self.radius = radius

    def move(self):
        self.x += self.dx
        self.y += self.dy
        if self.left < 0 or self.right > SCREEN_WIDTH:
            self.dx *= -1
            play_sound(bounce_sound)
        if self.top < 0:
            self.dy *= -1
            play_sound(bounce_sound)

    def reset_position(self):
        self.x = SCREEN_WIDTH // 2 - self.radius
        self.y = SCREEN_HEIGHT - PADDLE_HEIGHT - (self.radius * 3)
        self.dx = self.original_speed_x
        self.dy = self.original_speed_y

    def change_speed(self, new_dx, new_dy):
        self.dx = new_dx if new_dx is not None else self.dx
        self.dy = new_dy if new_dy is not None else self.dy

class Brick(pygame.Rect):
    def __init__(self, x, y, width, height, brick_type=1):
        super().__init__(x, y, width, height)
        self.hits = brick_type
        self.original_hits = brick_type
        self.color = BLUE if brick_type == 1 else RED if brick_type == 2 else (100, 100, 100)
        self.is_destroyed = False

    def hit(self):
        if self.hits > 0:
            self.hits -= 1
            if self.hits == 0:
                self.is_destroyed = True
                return True
        return False

class PowerUp(pygame.Rect):
    def __init__(self, x, y, type):
        super().__init__(x, y, 30, 30)
        self.type = type
        self.speed = 6
        self.color = YELLOW
        if self.type == 'longer_paddle': self.color = GREEN
        elif self.type == 'multi_ball': self.color = WHITE
        elif self.type == 'slow_ball': self.color = BLUE

    def move(self):
        self.y += self.speed

# Sound helpers
def play_sound(sound):
    if not is_muted and sound:
        sound.play()

def toggle_mute():
    global is_muted
    is_muted = not is_muted
    if is_muted:
        pygame.mixer.music.pause()
        pygame.mixer.stop()
    else:
        pygame.mixer.music.unpause()

# UI drawing
def draw_text(surface, text, font, color, x, y):
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(center=(x, y))
    surface.blit(text_surface, text_rect)

def draw_button(surface, rect, text, font, color, hover_color):
    mouse_pos = pygame.mouse.get_pos()
    button_color = hover_color if rect.collidepoint(mouse_pos) else color
    pygame.draw.rect(surface, button_color, rect, border_radius=12)
    draw_text(surface, text, font, BLACK, rect.centerx, rect.centery)
    return rect.collidepoint(mouse_pos)

def draw_game_elements():
    screen.fill(BLACK)
    pygame.draw.rect(screen, WHITE, paddle)
    for ball in balls:
        pygame.draw.circle(screen, WHITE, ball.center, ball.radius)
    for brick in bricks:
        if not brick.is_destroyed:
            pygame.draw.rect(screen, brick.color, brick)
    for pu in power_ups:
        pygame.draw.rect(screen, pu.color, pu)
    draw_text(screen, f"Score: {player_score}", font_small, WHITE, 100, 20)
    draw_text(screen, f"Lives: {player_lives}", font_small, WHITE, SCREEN_WIDTH // 2, 20)
    draw_text(screen, f"Level: {current_level_num + 1}", font_small, WHITE, SCREEN_WIDTH - 100, 20)

# Game logic
def load_level(level_num):
    global bricks, balls, power_ups
    bricks = []
    power_ups = []
    balls.clear()
    balls.append(Ball(SCREEN_WIDTH // 2, SCREEN_HEIGHT - PADDLE_HEIGHT - 40, BALL_RADIUS))
    paddle.resize(PADDLE_WIDTH)
    paddle.x = SCREEN_WIDTH // 2 - paddle.width // 2
    if level_num >= len(LEVELS):
        return False
    level_data = LEVELS[level_num]
    for row_idx, row in enumerate(level_data):
        for col_idx, brick_type in enumerate(row):
            if brick_type != 0:
                brick_x = col_idx * (BRICK_WIDTH + 5) + (SCREEN_WIDTH - len(row) * (BRICK_WIDTH + 5)) // 2
                brick_y = row_idx * (BRICK_HEIGHT + 5) + 50
                bricks.append(Brick(brick_x, brick_y, BRICK_WIDTH, BRICK_HEIGHT, brick_type))
    return True

def reset_game():
    global player_lives, player_score, current_level_num, current_game_state
    player_lives = 3
    player_score = 0
    current_level_num = 0
    load_level(current_level_num)
    current_game_state = GAME_STATE_PLAYING

# Game state
LEVELS = [
    [[1]*10]*3,
    [[0, 1, 1, 0, 0, 0, 0, 1, 1, 0], [1, 2, 1, 1, 1, 1, 1, 1, 2, 1], [0, 1, 0, 2, 2, 2, 2, 0, 1, 0], [0, 0, 0, 1, 1, 1, 1, 0, 0, 0]],
    [[99, 99, 1, 1, 1, 1, 1, 1, 99, 99], [99, 1, 1, 2, 2, 2, 2, 1, 1, 99], [1, 1, 1, 1, 1, 1, 1, 1, 1, 1], [1, 2, 1, 2, 1, 2, 1, 2, 1, 2]]
]

bricks = []
balls = []
power_ups = []
paddle = Paddle(SCREEN_WIDTH // 2 - PADDLE_WIDTH // 2, SCREEN_HEIGHT - PADDLE_HEIGHT - 30, PADDLE_WIDTH, PADDLE_HEIGHT)
balls.append(Ball(SCREEN_WIDTH // 2, SCREEN_HEIGHT - PADDLE_HEIGHT - 40, BALL_RADIUS))

# Input tracking
paddle_move_left = False
paddle_move_right = False
load_level(current_level_num)

# Main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT: paddle_move_left = True
            if event.key == pygame.K_RIGHT: paddle_move_right = True
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_LEFT: paddle_move_left = False
            if event.key == pygame.K_RIGHT: paddle_move_right = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            if current_game_state == GAME_STATE_TITLE:
                if pygame.Rect(SCREEN_WIDTH // 2 - 120, SCREEN_HEIGHT // 2, 240, 60).collidepoint(mx, my):
                    current_game_state = GAME_STATE_PLAYING
                if pygame.Rect(SCREEN_WIDTH - 130, 20, 120, 40).collidepoint(mx, my):
                    toggle_mute()
            elif current_game_state == GAME_STATE_GAME_OVER:
                if pygame.Rect(SCREEN_WIDTH // 2 - 110, SCREEN_HEIGHT // 2 + 60, 220, 50).collidepoint(mx, my):
                    reset_game()
                if pygame.Rect(SCREEN_WIDTH // 2 - 110, SCREEN_HEIGHT // 2 + 120, 220, 50).collidepoint(mx, my):
                    current_game_state = GAME_STATE_TITLE
        if event.type == pygame.USEREVENT + 1:
            paddle.resize(PADDLE_WIDTH)
            pygame.time.set_timer(pygame.USEREVENT + 1, 0)
        if event.type == pygame.USEREVENT + 2:
            for ball in balls:
                ball.change_speed(ball.original_speed_x, ball.original_speed_y)
            pygame.time.set_timer(pygame.USEREVENT + 2, 0)

    if current_game_state == GAME_STATE_TITLE:
        screen.fill(BLACK)
        draw_text(screen, "ARKANOID REMIX", font_large, YELLOW, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 150)
        draw_text(screen, "Press START to begin", font_small, WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 80)
        draw_button(screen, pygame.Rect(SCREEN_WIDTH // 2 - 120, SCREEN_HEIGHT // 2, 240, 60), "START GAME", font_medium, GREEN, (0, 200, 0))
        draw_button(screen, pygame.Rect(SCREEN_WIDTH - 130, 20, 120, 40), "UNMUTE" if is_muted else "MUTE", font_small, BLUE, (0, 0, 200))

    elif current_game_state == GAME_STATE_PLAYING:
        if paddle_move_left: paddle.move(-1)
        if paddle_move_right: paddle.move(1)

        for ball in balls[:]:
            ball.move()
            if ball.colliderect(paddle) and ball.dy > 0:
                ball.dy *= -1
                play_sound(bounce_sound)
                hit_pos = (ball.centerx - paddle.centerx) / (paddle.width / 2)
                ball.dx = hit_pos * 6

            for brick in bricks:
                if not brick.is_destroyed and ball.colliderect(brick):
                    if brick.hit():
                        player_score += 10
                        if brick.hits == 0 and pygame.time.get_ticks() % 100 < 20:
                            types = ['longer_paddle', 'multi_ball', 'slow_ball']
                            power_ups.append(PowerUp(brick.centerx, brick.centery, random.choice(types)))
                    ball.dy *= -1
                    break

            bricks = [b for b in bricks if not b.is_destroyed]
            if ball.top > SCREEN_HEIGHT:
                balls.remove(ball)
                if not balls:
                    player_lives -= 1
                    if player_lives <= 0:
                        current_game_state = GAME_STATE_GAME_OVER
                    else:
                        balls.append(Ball(SCREEN_WIDTH // 2, SCREEN_HEIGHT - PADDLE_HEIGHT - 40, BALL_RADIUS))
                        paddle.resize(paddle.original_width)
                        paddle.x = SCREEN_WIDTH // 2 - paddle.width // 2

        for pu in power_ups[:]:
            pu.move()
            if pu.colliderect(paddle):
                if pu.type == 'longer_paddle':
                    paddle.resize(PADDLE_WIDTH * 1.5)
                    pygame.time.set_timer(pygame.USEREVENT + 1, 5000)
                elif pu.type == 'multi_ball':
                    balls.append(Ball(paddle.centerx - 20, paddle.top - BALL_RADIUS, BALL_RADIUS))
                    balls[-1].dx *= -1
                    balls.append(Ball(paddle.centerx + 20, paddle.top - BALL_RADIUS, BALL_RADIUS))
                elif pu.type == 'slow_ball':
                    for ball in balls:
                        ball.change_speed(ball.dx * 0.5, ball.dy * 0.5)
                    pygame.time.set_timer(pygame.USEREVENT + 2, 7000)
                power_ups.remove(pu)
            elif pu.top > SCREEN_HEIGHT:
                power_ups.remove(pu)

        if not bricks:
            current_level_num += 1
            if not load_level(current_level_num):
                current_game_state = GAME_STATE_TITLE
                reset_game()

        draw_game_elements()

    elif current_game_state == GAME_STATE_GAME_OVER:
        screen.fill(BLACK)
        draw_text(screen, "GAME OVER", font_large, RED, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 120)
        draw_text(screen, f"Final Score: {player_score}", font_medium, WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50)
        draw_text(screen, "Try Again or Return to Menu", font_small, WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 10)
        draw_button(screen, pygame.Rect(SCREEN_WIDTH // 2 - 110, SCREEN_HEIGHT // 2 + 60, 220, 50), "RETRY", font_medium, GREEN, (0, 200, 0))
        draw_button(screen, pygame.Rect(SCREEN_WIDTH // 2 - 110, SCREEN_HEIGHT // 2 + 120, 220, 50), "MAIN MENU", font_medium, BLUE, (0, 0, 200))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
