import pygame
import sys

from tetromino import Tetromino

LEFT_SIDEBAR_WIDTH = 200

# Grid dimensions
TOP_PADDING = 50
BOTTOM_PADDING = 50
GRID_SIZE = 30
GRID_WIDTH = 10
GRID_HEIGHT = 20

# Preview area dimensions
PREVIEW_WIDTH = 4
PREVIEW_HEIGHT = 4
PREVIEW_OFFSET_X = 50
PREVIEW_OFFSET_Y = 50

# Pause button dimensions
PAUSE_WIDTH = 100
PAUSE_HEIGHT = 50
PAUSE_OFFSET_X = 50
PAUSE_OFFSET_Y = 300

RESTART_WIDTH = 100
RESTART_HEIGHT = 50
RESTART_OFFSET_X = 50
RESTART_OFFSET_Y = 400

# Screen dimensions
SCREEN_WIDTH = LEFT_SIDEBAR_WIDTH + GRID_SIZE * (PREVIEW_WIDTH + GRID_WIDTH) + 100
SCREEN_HEIGHT = GRID_SIZE * GRID_HEIGHT + TOP_PADDING + BOTTOM_PADDING

SCORE_FACTORS = [0, 40, 100, 300, 1200]
LINES_PER_LEVEL = 10

# Colors
WHITE = (255, 255, 255)
GRAY = (100, 100, 100)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)


class TetrisGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Tetris")
        self.rounds = 0
        self.record_level = 0
        self.record_lines = 0
        self.record_score = 0
        self.reset()

    def reset(self):
        self.clock = pygame.time.Clock()
        self.fall_time = 0
        self.fall_speed = 500
        self.locked_positions = {}
        self.score = 0
        self.total_lines_cleared = 0
        self.is_paused = False
        self.level = 1
        self.tetromino = Tetromino(GRID_WIDTH // 2 - 2, -1)
        self.next_tetrominos = self.get_next_tetrominos(5)
        self.update_grid()

    def update_grid(self):
        self.grid = [[self.locked_positions.get((x, y), BLACK) for x in range(GRID_WIDTH)] for y in range(GRID_HEIGHT)]

    def draw_grid(self):
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                pygame.draw.rect(
                    self.screen,
                    self.grid[y][x],
                    (LEFT_SIDEBAR_WIDTH + x * GRID_SIZE, TOP_PADDING + y * GRID_SIZE, GRID_SIZE, GRID_SIZE),
                    0,
                )
                pygame.draw.rect(
                    self.screen,
                    GRAY,
                    (LEFT_SIDEBAR_WIDTH + x * GRID_SIZE, TOP_PADDING + y * GRID_SIZE, GRID_SIZE, GRID_SIZE),
                    1,
                )

    def draw_tetromino(self):
        for x, y in self.tetromino.enumerate_cells():
            pygame.draw.rect(
                self.screen,
                self.tetromino.shape.color,
                (
                    LEFT_SIDEBAR_WIDTH + (self.tetromino.x + x) * GRID_SIZE,
                    TOP_PADDING + (self.tetromino.y + y) * GRID_SIZE,
                    GRID_SIZE,
                    GRID_SIZE,
                ),
                0,
            )
            pygame.draw.rect(
                self.screen,
                GRAY,
                (
                    LEFT_SIDEBAR_WIDTH + (self.tetromino.x + x) * GRID_SIZE,
                    TOP_PADDING + (self.tetromino.y + y) * GRID_SIZE,
                    GRID_SIZE,
                    GRID_SIZE,
                ),
                1,
            )

    def valid_move(self):
        for x, y in self.tetromino.enumerate_cells():
            if (
                self.tetromino.x + x < 0
                or self.tetromino.x + x >= GRID_WIDTH
                or self.tetromino.y + y >= GRID_HEIGHT
                or self.grid[self.tetromino.y + y][self.tetromino.x + x] != BLACK
            ):
                return False

        return True

    def clear_lines(self):
        lines_cleared = 0
        # To do: opportunity to shortcut.
        for y in reversed(range(GRID_HEIGHT)):
            if all((x, y) in self.locked_positions for x in range(GRID_WIDTH)):
                for x in range(GRID_WIDTH):
                    del self.locked_positions[(x, y)]
                lines_cleared += 1
            elif lines_cleared > 0:
                for x in range(GRID_WIDTH):
                    if (x, y) not in self.locked_positions:
                        continue
                    value = self.locked_positions.pop((x, y))
                    self.locked_positions[(x, y + lines_cleared)] = value

        return lines_cleared

    def get_next_tetrominos(self, num):
        return [Tetromino(GRID_WIDTH // 2 - 2, 0) for _ in range(num)]

    def rotate_next(self):
        self.tetromino = self.next_tetrominos.pop(0)
        self.next_tetrominos.extend(self.get_next_tetrominos(1))

    def draw_preview(self):
        for i, tetromino in enumerate(self.next_tetrominos):
            for x, y in tetromino.enumerate_cells():
                pygame.draw.rect(
                    self.screen,
                    tetromino.shape.color,
                    (
                        LEFT_SIDEBAR_WIDTH + GRID_WIDTH * GRID_SIZE + PREVIEW_OFFSET_X + x * GRID_SIZE,
                        PREVIEW_OFFSET_Y + i * GRID_SIZE * PREVIEW_HEIGHT + y * GRID_SIZE,
                        GRID_SIZE,
                        GRID_SIZE,
                    ),
                    0,
                )
                pygame.draw.rect(
                    self.screen,
                    GRAY,
                    (
                        LEFT_SIDEBAR_WIDTH + GRID_WIDTH * GRID_SIZE + PREVIEW_OFFSET_X + x * GRID_SIZE,
                        PREVIEW_OFFSET_Y + i * GRID_SIZE * PREVIEW_HEIGHT + y * GRID_SIZE,
                        GRID_SIZE,
                        GRID_SIZE,
                    ),
                    1,
                )

    def draw_pause_button(self):
        button_color = RED if self.is_paused else GREEN
        pygame.draw.rect(self.screen, button_color, (PAUSE_OFFSET_X, PAUSE_OFFSET_Y, PAUSE_WIDTH, PAUSE_HEIGHT), 0)
        pygame.draw.rect(self.screen, WHITE, (PAUSE_OFFSET_X, PAUSE_OFFSET_Y, PAUSE_WIDTH, PAUSE_HEIGHT), 1)
        font = pygame.font.Font(None, 24)
        text = font.render("Pause" if not self.is_paused else "Resume", True, WHITE)
        self.screen.blit(text, (PAUSE_OFFSET_X + 20, PAUSE_OFFSET_Y + 10))

    def is_pause_button_clicked(self, pos):
        x, y = pos
        return (PAUSE_OFFSET_X <= x <= PAUSE_OFFSET_X + PAUSE_WIDTH) and (
            PAUSE_OFFSET_Y <= y <= PAUSE_OFFSET_Y + PAUSE_HEIGHT
        )

    def draw_stat(self, text, y):
        font = pygame.font.Font(None, 24)
        text = font.render(text, True, WHITE)
        self.screen.blit(text, (20, y))

    def update_records_and_restart(self):
        self.rounds += 1
        self.record_level = max(self.record_level, self.level)
        self.record_lines = max(self.record_lines, self.total_lines_cleared)
        self.record_score = max(self.record_score, self.score)
        self.reset()

    def run(self):
        while True:
            self.fall_time += self.clock.get_rawtime()
            self.clock.tick()

            # Tetromino movement
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.is_pause_button_clicked(pygame.mouse.get_pos()):
                        self.is_paused = not self.is_paused
                elif event.type == pygame.KEYDOWN and not self.is_paused:
                    if event.key == pygame.K_LEFT:
                        self.tetromino.x -= 1
                        if not self.valid_move():
                            self.tetromino.x += 1
                    if event.key == pygame.K_RIGHT:
                        self.tetromino.x += 1
                        if not self.valid_move():
                            self.tetromino.x -= 1
                    if event.key == pygame.K_DOWN:
                        self.tetromino.y += 1
                        if not self.valid_move():
                            self.tetromino.y -= 1
                    if event.key == pygame.K_SPACE:
                        while self.valid_move():
                            self.tetromino.y += 1
                        self.tetromino.y -= 1
                    if event.key == pygame.K_UP:
                        self.tetromino.rotate()
                        if not self.valid_move():
                            self.tetromino.unrotate()

            # Tetromino falling
            if self.fall_time > self.fall_speed and not self.is_paused:
                self.fall_time = 0
                self.tetromino.y += 1
                if not self.valid_move():
                    self.tetromino.y -= 1
                    for x, y in self.tetromino.enumerate_cells():
                        self.locked_positions[(self.tetromino.x + x, self.tetromino.y + y)] = self.tetromino.shape.color

                    lines_cleared = self.clear_lines()
                    self.score += SCORE_FACTORS[lines_cleared] * self.level

                    self.total_lines_cleared += lines_cleared
                    self.level = self.total_lines_cleared // LINES_PER_LEVEL + 1

                    self.update_grid()
                    self.rotate_next()

                    if not self.valid_move():
                        self.update_records_and_restart()
                        continue

                    self.fall_speed = 500 / (1 + (self.level - 1) * 0.2)

            # Drawing
            self.screen.fill(BLACK)
            self.draw_grid()
            self.draw_tetromino()
            self.draw_preview()
            self.draw_pause_button()
            self.draw_stat(f"Level: {self.level}", 50)
            self.draw_stat(f"Lines: {self.total_lines_cleared}", 100)
            self.draw_stat(f"Score: {self.score}", 150)
            self.draw_stat(f"Interval: {self.fall_speed:.0f}", 200)
            self.draw_stat("RECORDS", 450)
            self.draw_stat(f"Rounds: {self.rounds}", 500)
            self.draw_stat(f"Level: {self.record_level}", 550)
            self.draw_stat(f"Lines: {self.record_lines}", 600)
            self.draw_stat(f"Score: {self.record_score}", 650)
            pygame.display.update()


if __name__ == "__main__":
    pygame.init()
    game = TetrisGame()
    game.run()
