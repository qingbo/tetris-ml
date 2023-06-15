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
     ["..O.",
      "..O.",
      ".OO.",
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
     [".O..",
      ".O..",
      ".O..",
      ".O.."]]
]
# fmt: on

COLORS = [(192, 73, 188), (170, 105, 62), (77, 64, 159), (177, 156, 70), (173, 225, 81), (167, 63, 64), (93, 178, 135)]


class Shape:
    def __init__(self, variants, color):
        self.rotations = [[[c == "O" for c in row] for row in v] for v in variants]
        self.color = color

    def num_rotations(self):
        return len(self.rotations)


SHAPES = [Shape(variants, color) for variants, color in zip(SHAPE_VISUALS, COLORS)]


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
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.shape = RANDOM_BAG.next()
        self.rotation = 0  # random.randrange(0, self.shape.num_rotations())

    def rotate(self):
        self.rotation = (self.rotation + 1) % self.shape.num_rotations()

    def unrotate(self):
        self.rotation = (self.rotation - 1) % self.shape.num_rotations()

    def enumerate_cells(self):
        for y, row in enumerate(self.shape.rotations[self.rotation]):
            for x, cell in enumerate(row):
                if cell:
                    yield x, y
