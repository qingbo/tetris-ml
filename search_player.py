import time
from tetris import TetrisGame, GRID_WIDTH, GRID_HEIGHT
from tetromino import Tetromino

SPAWN_X = GRID_WIDTH // 2 - 2


def is_valid_position(game: TetrisGame, tetromino: Tetromino):
    for x, y in tetromino.enumerate_cells():
        if (
            tetromino.x + x < 0
            or tetromino.x + x >= GRID_WIDTH
            or tetromino.y + y >= GRID_HEIGHT
            or (tetromino.x + x, tetromino.y + y) in game.locked_positions
        ):
            return False

    return True


def calculate_cost(game: TetrisGame, tetromino: Tetromino):
    locked_positions = dict(game.locked_positions)
    for x, y in tetromino.enumerate_cells():
        locked_positions[(tetromino.x + x, tetromino.y + y)] = tetromino.shape.color

    # Try to clear lines first.
    lines_cleared = 0
    for y in reversed(range(GRID_HEIGHT)):
        if all((x, y) in locked_positions for x in range(GRID_WIDTH)):
            for x in range(GRID_WIDTH):
                del locked_positions[(x, y)]
            lines_cleared += 1
        elif lines_cleared > 0:
            for x in range(GRID_WIDTH):
                if (x, y) not in locked_positions:
                    continue
                value = locked_positions.pop((x, y))
                locked_positions[(x, y + lines_cleared)] = value

    num_holes = 0
    bumpiness = 0
    column_heights = []
    for x in range(GRID_WIDTH):
        found_locked_pos = False
        for y in range(GRID_HEIGHT):
            if (x, y) in locked_positions:
                if not found_locked_pos:
                    found_locked_pos = True
                    column_heights.append(GRID_HEIGHT - y)
            elif found_locked_pos:
                num_holes += 1
        if not found_locked_pos:
            column_heights.append(0)

    for i in range(1, len(column_heights)):
        bumpiness += abs(column_heights[i] - column_heights[i - 1])
    total_height = sum(column_heights)
    cost = total_height + bumpiness * 2 + num_holes * 20
    return cost


def find_lowest_cost(game: TetrisGame):
    min_cost = 10000
    best_r, best_x = 0, 0
    # Check each rotation.
    for r in range(game.falling.shape.num_rotations()):
        # Make a copy.
        tetromino = game.falling.rotated_copy(r)
        initial_y = tetromino.y
        # Try from left to right.
        for x in range(-tetromino.rotation_info.left, GRID_WIDTH - tetromino.rotation_info.right):
            tetromino.x = x
            tetromino.y = initial_y

            while is_valid_position(game, tetromino):
                tetromino.y += 1
            tetromino.y -= 1

            cost = calculate_cost(game, tetromino)
            if cost < min_cost:
                min_cost = cost
                best_r, best_x = r, x
    return best_r, best_x


def main():
    game = TetrisGame(training_mode=True)

    for i in range(1000):
        rotate, column = find_lowest_cost(game)
        game.step(rotate, column, 0.2)


if __name__ == "__main__":
    main()
