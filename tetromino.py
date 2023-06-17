import random

# fmt: off
# Tetromino shapes
SHAPE_VISUALS = [
    [[".O..",
      "OOO.",
      "....",
      "...."],
     [".O..",
      ".OO.",
      ".O..",
      "...."],
     ["....",
      "OOO.",
      ".O..",
      "...."],
     [".O..",
      "OO..",
      ".O..",
      "...."]],
    [["..O.",
      "OOO.",
      "....",
      "...."],
     [".O..",
      ".O..",
      ".OO.",
      "...."],
     ["....",
      "OOO.",
      "O...",
      "...."],
     ["OO..",
      ".O..",
      ".O..",
      "...."]],
    [["O...",
      "OOO.",
      "....",
      "...."],
     [".OO.",
      ".O..",
      ".O..",
      "...."],
     ["....",
      "OOO.",
      "..O.",
      "...."],
     [".O..",
      ".O..",
      "OO..",
      "...."]],
    [["....",
      ".OO.",
      ".OO.",
      "...."]],
    [["....",
      ".OO.",
      "OO..",
      "...."],
     [".O..",
      ".OO.",
      "..O.",
      "...."]],
    [["....",
      "OO..",
      ".OO.",
      "...."],
     ["..O.",
      ".OO.",
      ".O..",
      "...."]],
    [["....",
      "OOOO",
      "....",
      "...."],
     ["..O.",
      "..O.",
      "..O.",
      "..O."]]
]
# fmt: on

COLORS = [(192, 73, 188), (170, 105, 62), (77, 64, 159), (177, 156, 70), (173, 225, 81), (167, 63, 64), (93, 178, 135)]


class RotationInfo:
    def __init__(self, visual):
        self.matrix = [[c == "O" for c in row] for row in visual]
        left, right = 3, 0
        for row in self.matrix:
            for x, filled in enumerate(row):
                if not filled:
                    continue
                left = min(left, x)
                right = max(right, x)
        self.left = left
        self.right = right


class Shape:
    def __init__(self, variants, color, index):
        self.rotations = [RotationInfo(v) for v in variants]
        self.color = color
        self.index = index

    def num_rotations(self):
        return len(self.rotations)


SHAPES = [Shape(variants, color, i) for i, (variants, color) in enumerate(zip(SHAPE_VISUALS, COLORS))]


# 7-bag - https://simon.lc/the-history-of-tetris-randomizers
class Shape7Bag:
    def __init__(self) -> None:
        self.bag: Shape = []

    def next(self):
        if not self.bag:
            self.bag = list(SHAPES)
            random.shuffle(self.bag)

        return self.bag.pop(0)


RANDOM_BAG = Shape7Bag()


class Tetromino:
    def __init__(self, x, y, shape=None, rotation=0):
        self.x = x
        self.y = y
        self.shape = shape if shape else RANDOM_BAG.next()
        self.rotation = rotation
        self.rotation_info = self.shape.rotations[self.rotation]

    def rotate(self):
        self.rotation = (self.rotation + 1) % self.shape.num_rotations()
        self.rotation_info = self.shape.rotations[self.rotation]

    def unrotate(self):
        self.rotation = (self.rotation - 1) % self.shape.num_rotations()
        self.rotation_info = self.shape.rotations[self.rotation]

    def enumerate_cells(self):
        for y, row in enumerate(self.rotation_info.matrix):
            for x, cell in enumerate(row):
                if cell:
                    yield x, y

    def rotated_copy(self, rotation):
        return Tetromino(self.x, self.y, self.shape, rotation)
