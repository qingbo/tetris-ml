# Tetr.io

import random
import time
import timeit

import mss
import pyautogui
import pygame
from PIL import Image

from tetris import TetrisGame, GRID_WIDTH, GRID_HEIGHT
from tetromino import Tetromino, SHAPES

TETRIO_BLACK = (9, 7, 5)
# Passed to mss.grab - reduced scale.
GAME_AREA = (550, 158, 1200, 865)  # Board: (707, 250, 1022, 865)
# Image size - twice as large.
CELL_SIZE = 61.5
TETROMINO_SAMPLE_RADIUS = int(CELL_SIZE / 4)
NUM_SAMPLE_PIXELS = (TETROMINO_SAMPLE_RADIUS * 2) ** 2
PIECES_OFFSET_Y = 330
HOLD_OFFSET_X = 158
UPCOMING_OFFSET_X = 1142
UPCOMING_SPACE = 185.5

BOARD_OFFSET_X = 314
BOARD_OFFSET_Y = 184

IGNORE_ROWS = 8  # a hack.

SAMPLED_COLORS = [
    (158, 83, 156),
    (79, 52, 34),
    (43, 36, 72),
    (175, 158, 80),
    (147, 181, 82),
    (173, 75, 77),
    (99, 180, 142),
    (30, 30, 30),  # Nothing
]
COLOR_TO_SHAPE = dict(zip(SAMPLED_COLORS, SHAPES + [None]))


def nearly_black(color):
    return all([c < 30 for c in color])


def mean_color_near(im: Image, x, y):
    r, g, b = 0, 0, 0
    for i in range(int(x - TETROMINO_SAMPLE_RADIUS), int(x + TETROMINO_SAMPLE_RADIUS)):
        for j in range(int(y - TETROMINO_SAMPLE_RADIUS), int(y + TETROMINO_SAMPLE_RADIUS)):
            l, m, n = im.getpixel((i, j))
            r += l
            g += m
            b += n
    return r // NUM_SAMPLE_PIXELS, g // NUM_SAMPLE_PIXELS, b // NUM_SAMPLE_PIXELS
    # return im.crop(
    #     (
    #         x - TETROMINO_SAMPLE_RADIUS,
    #         y - TETROMINO_SAMPLE_RADIUS,
    #         x + TETROMINO_SAMPLE_RADIUS,
    #         y + TETROMINO_SAMPLE_RADIUS,
    #     )
    # )


def square_distance(c1, c2):
    return (c1[0] - c2[0]) ** 2 + (c1[1] - c2[1]) ** 2 + (c1[2] - c2[2]) ** 2


def map_color_to_shape(sample_color):
    distance_min = 3 * (256**2)
    best_guess = None
    for color, shape in COLOR_TO_SHAPE.items():
        distance = square_distance(sample_color, color)
        if distance < distance_min:
            distance_min = distance
            best_guess = shape
    return best_guess


def press_keys(seq):
    for key in seq:
        pyautogui.press(key)
        time.sleep(random.uniform(0.08, 0.15))


def take_action(rotate, column):
    seq = []
    for _ in range(rotate):
        seq.append("up")

    movement = column - 3
    if movement != 0:
        distance = abs(movement)
        key = "left" if movement < 0 else "right"
        for _ in range(distance):
            seq.append(key)
    seq.append("space")

    press_keys(seq)


class TetrioProxy:
    def __init__(self, game: TetrisGame):
        self.game = game

    def mirror_board(self):
        sct = mss.mss()
        old_next = None
        old_next_shape_indexes = None
        while True:
            locked_positions = {}
            start = timeit.default_timer()
            raw = sct.grab(GAME_AREA)
            screenshot = Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")
            screenshot_duration = timeit.default_timer() - start

            pixel_x = BOARD_OFFSET_X + 30
            for x in range(GRID_WIDTH):
                pixel_y = BOARD_OFFSET_Y + 30
                for y in range(GRID_HEIGHT):
                    if y >= IGNORE_ROWS:
                        pixel_color = screenshot.getpixel((pixel_x, pixel_y))
                        if not nearly_black(pixel_color):
                            locked_positions[(x, y)] = pixel_color
                    pixel_y += CELL_SIZE
                pixel_x += CELL_SIZE
            game.locked_positions = locked_positions
            game.update_grid()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    break

            # Figure out the held piece.
            mean_color = mean_color_near(screenshot, HOLD_OFFSET_X, PIECES_OFFSET_Y)
            shape = map_color_to_shape(mean_color)
            game.held = Tetromino(0, 0, shape)

            next_tetrominos = []
            for i in range(5):
                mean_color = mean_color_near(screenshot, UPCOMING_OFFSET_X, PIECES_OFFSET_Y + UPCOMING_SPACE * i)
                shape = map_color_to_shape(mean_color)
                next_tetrominos.append(Tetromino(GRID_WIDTH // 2 - 2, -1, shape))
            next_shape_indexes = [t.shape.index for t in next_tetrominos]
            print(old_next_shape_indexes)
            print(next_shape_indexes)
            if old_next and old_next_shape_indexes != next_shape_indexes:
                # Upcoming list changed, meaning that one is falling down now.
                # print(f"old: {len(old_next)}; new: {len(next_tetrominos)}")
                # print([t.shape.index for t in old_next])
                # print([t.shape.index for t in next_tetrominos])
                game.falling = old_next[0]
                # print([t.shape.index for t in old_next])
                # print([t.shape.index for t in next_tetrominos])
                # print(old_next)
                # print(next_tetrominos)
                assert old_next_shape_indexes[1:] == next_shape_indexes[:-1]
                best_r, best_x = game.get_best_action()
                print(game.falling.shape.index)
                print(f"Best action: {best_r}#{best_x-3}. Time: {screenshot_duration:.3f}, {total_duration:.3f}")
                # time.sleep(3)
                take_action(best_r, best_x)
            old_next = next_tetrominos
            old_next_shape_indexes = next_shape_indexes
            game.next_tetrominos = next_tetrominos

            game.update_screen()
            total_duration = timeit.default_timer() - start
            # hold_sample = sample_image(screenshot, UPCOMING_OFFSET_X, PIECES_OFFSET_Y + UPCOMING_SPACE * (i % 5))
            # pygame_image = pygame.image.fromstring(hold_sample.tobytes(), hold_sample.size, hold_sample.mode)
            # game.screen.blit(pygame_image, (0, 0))
            # pygame.display.update()
            # i += 1
            time.sleep(random.uniform(0.1, 0.2))


if __name__ == "__main__":
    game = TetrisGame(training_mode=True, mirror_mode=True)
    proxy = TetrioProxy(game)
    proxy.mirror_board()
