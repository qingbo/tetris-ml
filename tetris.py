import random
import pygame
import time
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
    def __init__(self, training_mode=False):
        self.training_mode = training_mode

        pygame.init()
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

        # Useful for training
        self.holes = 0
        self.bumpiness = 0

    def update_grid(self):
        self.grid = [[self.locked_positions.get((x, y), BLACK) for x in range(GRID_WIDTH)] for y in range(GRID_HEIGHT)]

    def draw_grid(self):
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                self.draw_rect(
                    (LEFT_SIDEBAR_WIDTH + x * GRID_SIZE, TOP_PADDING + y * GRID_SIZE, GRID_SIZE, GRID_SIZE),
                    self.grid[y][x],
                    GRAY,
                )

    def draw_tetromino(self):
        for x, y in self.tetromino.enumerate_cells():
            self.draw_rect(
                (
                    LEFT_SIDEBAR_WIDTH + (self.tetromino.x + x) * GRID_SIZE,
                    TOP_PADDING + (self.tetromino.y + y) * GRID_SIZE,
                    GRID_SIZE,
                    GRID_SIZE,
                ),
                self.tetromino.shape.color,
                GRAY,
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

    def complete_fall(self):
        for x, y in self.tetromino.enumerate_cells():
            self.locked_positions[(self.tetromino.x + x, self.tetromino.y + y)] = self.tetromino.shape.color

        lines_cleared = self.clear_lines()
        score_earned = SCORE_FACTORS[lines_cleared] * self.level
        self.score += score_earned

        self.total_lines_cleared += lines_cleared
        # Increase level/speed.
        self.level = 1 if self.training_mode else self.total_lines_cleared // LINES_PER_LEVEL + 1

        self.update_grid()
        self.rotate_upcoming()

        orig_holes = self.holes
        orig_bumpiness = self.bumpiness
        self.count_holes()
        self.calculate_bumpiness()
        increased_holes = self.holes - orig_holes
        increased_bumpiness = self.bumpiness - orig_bumpiness
        self.reward = score_earned - (increased_holes * 2) - (increased_bumpiness - 3)
        # print(f"{self.reward}: bumpiness {orig_bumpiness} -> {self.bumpiness}")

        self.fall_speed = 500 / (1 + (self.level - 1) * 0.2)

        if not self.valid_move():
            self.update_records_and_restart()
        # print(f"Holes: {self.count_holes()}")
        # print(f"Bumpiness: {self.calculate_bumpiness()}")

    def get_next_tetrominos(self, num):
        return [Tetromino(GRID_WIDTH // 2 - 2, 0) for _ in range(num)]

    def rotate_upcoming(self):
        self.tetromino = self.next_tetrominos.pop(0)
        self.next_tetrominos.extend(self.get_next_tetrominos(1))

    def draw_rect(self, rect, color, border_color):
        pygame.draw.rect(self.screen, color, rect, 0)
        pygame.draw.rect(self.screen, border_color, rect, 1)

    def draw_preview(self):
        for i, tetromino in enumerate(self.next_tetrominos):
            for x, y in tetromino.enumerate_cells():
                self.draw_rect(
                    (
                        LEFT_SIDEBAR_WIDTH + GRID_WIDTH * GRID_SIZE + PREVIEW_OFFSET_X + x * GRID_SIZE,
                        PREVIEW_OFFSET_Y + i * GRID_SIZE * PREVIEW_HEIGHT + y * GRID_SIZE,
                        GRID_SIZE,
                        GRID_SIZE,
                    ),
                    tetromino.shape.color,
                    GRAY,
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

    def update_screen(self):
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

    def move_h(self, direction):
        self.tetromino.x += direction
        if not self.valid_move():
            self.tetromino.x -= direction

    def count_holes(self):
        num_holes = 0
        for x in range(GRID_WIDTH):
            found_locked_pos = False
            for y in range(GRID_HEIGHT):
                if (x, y) in self.locked_positions:
                    found_locked_pos = True
                elif found_locked_pos:
                    num_holes += 1
        self.holes = num_holes
        return num_holes

    def calculate_bumpiness(self):
        bumpiness = 0
        column_heights = []

        for x in range(GRID_WIDTH):
            height = 0
            for y in range(GRID_HEIGHT):
                if (x, y) in self.locked_positions:
                    height = GRID_HEIGHT - y
                    break
            column_heights.append(height)

        for i in range(1, len(column_heights)):
            bumpiness += abs(column_heights[i] - column_heights[i - 1])

        self.bumpiness = bumpiness
        return bumpiness

    def run(self):
        while True:
            self.fall_time += self.clock.get_rawtime()
            self.clock.tick()

            # Tetromino movement
            space_pressed = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.is_pause_button_clicked(pygame.mouse.get_pos()):
                        self.is_paused = not self.is_paused
                elif event.type == pygame.KEYDOWN and not self.is_paused:
                    if event.key == pygame.K_LEFT:
                        self.move_h(-1)
                    if event.key == pygame.K_RIGHT:
                        self.move_h(1)
                    if event.key == pygame.K_DOWN:
                        self.tetromino.y += 1
                        if not self.valid_move():
                            self.tetromino.y -= 1
                    if event.key == pygame.K_SPACE:
                        space_pressed = True
                        while self.valid_move():
                            self.tetromino.y += 1
                        self.tetromino.y -= 1
                        self.complete_fall()
                    if event.key == pygame.K_UP:
                        self.tetromino.rotate()
                        if not self.valid_move():
                            self.tetromino.unrotate()

            # Tetromino falling
            if self.fall_time > self.fall_speed and not self.is_paused and not space_pressed:
                self.fall_time = 0
                self.tetromino.y += 1
                if not self.valid_move():
                    self.tetromino.y -= 1
                    self.complete_fall()

            # Drawing
            self.update_screen()

    def step(self, rotate, column, delay=1):
        orig_score, orig_holes, orig_bumpiness = self.score, self.holes, self.bumpiness

        # Rotate.
        for _ in range(rotate):
            self.tetromino.rotate()

        # Move.
        movement = column - 3
        if movement != 0:
            distance = abs(movement)
            direction = movement // distance
            for _ in range(distance):
                self.move_h(direction)

        # Fall.
        while self.valid_move():
            self.tetromino.y += 1
        self.tetromino.y -= 1
        self.complete_fall()

        self.count_holes()
        self.calculate_bumpiness()

        # Calculate reward
        # Consider game reset

        if delay:
            for event in pygame.event.get():
                pass
            self.update_screen()
            time.sleep(delay)


if __name__ == "__main__":
    game = TetrisGame()
    game.run()
    # for _ in range(10):
    #     rotate = random.randint(0, 3)
    #     column = random.randint(0, 9)
    #     game.step(rotate, column)
