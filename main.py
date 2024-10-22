from collections import namedtuple
from pixoo import Pixoo, Palette
import time
import multiprocessing
import math

TOTAL_CPU = multiprocessing.cpu_count()
PIXOO_SIZE = 64
SQUARE_SIZE = int(math.sqrt(PIXOO_SIZE * PIXOO_SIZE / TOTAL_CPU))
STAT_FILENAME = "/proc/stat"
UTILISATION_PERCENT_THRESHOLD = 3
SLEEP_DURATION = 1

Point = namedtuple("Point", ["x", "y"])
Color = namedtuple("Color", ["r", "g", "b"])
Square = namedtuple("Square", ["top_left", "bottom_right"])
CPUState = namedtuple("CPUState", ["last_idle", "last_total"])


def color_squares(
    pixoo: Pixoo, highlight_mask: list[bool], squares: list[Square], color: Color
):
    for i in range(TOTAL_CPU):
        square = squares[i]
        if highlight_mask[i]:
            pixoo.draw_filled_rectangle(square.top_left, square.bottom_right, color)
        else:
            pixoo.draw_filled_rectangle(
                square.top_left, square.bottom_right, Palette.BLACK
            )
    pixoo.push()


def build_squares() -> list[Square]:
    squares = []
    x, y = 0, 0
    for i in range(
        4
    ):  # TODO: This needs to be calculated based on the size of the square
        ub_y = y + SQUARE_SIZE
        if i == 0:
            ub_y -= 1
        for j in range(4):
            ub_x = x + SQUARE_SIZE
            if j == 0:
                ub_x -= 1
            squares.append(Square(Point(x + 1, y + 1), Point(ub_x - 1, ub_y - 1)))
            x = ub_x
        x = 0
        y = ub_y
    return squares


class CPUHighlightMaskReader:
    def __init__(self):
        self.cpu_states = [CPUState(0, 0) for i in range(TOTAL_CPU)]

    def __enter__(self):
        self.f = open(STAT_FILENAME)
        return self

    def get_mask(self):
        highlight_mask = [False for i in range(TOTAL_CPU)]

        self.f.seek(0)
        # Skip the first line
        self.f.readline()
        # Read the next TOTAL_CPU lines
        for i in range(TOTAL_CPU):
            state = self.cpu_states[i]

            fields = [float(column) for column in self.f.readline().strip().split()[1:]]
            idle, total = fields[3], sum(fields)
            idle_delta, total_delta = idle - state.last_idle, total - state.last_total
            self.cpu_states[i] = CPUState(idle, total)
            utilisation = 100.0 * (1.0 - idle_delta / total_delta)
            if utilisation > UTILISATION_PERCENT_THRESHOLD:
                highlight_mask[i] = True
            else:
                highlight_mask[i] = False
        return highlight_mask

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.f.close()


if __name__ == "__main__":
    pixoo = Pixoo("mock-ip", size=PIXOO_SIZE, simulated=True)
    squares = build_squares()
    red = Color(255, 0, 0)
    with CPUHighlightMaskReader() as mask_reader:
        while True:
            try:
                highlight_mask = mask_reader.get_mask()
                color_squares(pixoo, highlight_mask, squares, red)
                time.sleep(SLEEP_DURATION)
            except KeyboardInterrupt:
                break
