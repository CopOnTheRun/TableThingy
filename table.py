#standard functional
from __future__ import annotations
from dataclasses import dataclass
from itertools import cycle, zip_longest
from collections import defaultdict

#typing
from typing import Any
from collections.abc import Generator, Iterable

def h_pad(text: str, width: int, align: float, fill: str = " ") -> str:
    padding = width - len(text)
    lpad = round(align*padding)
    rpad = padding - lpad
    return f"{lpad*fill}{text}{rpad*fill}\n"

def str_height(text: str) -> int:
    return text.count("\n") + 1 if text else 0

def line_iter(content: Any) -> Generator[str, None, None]:
    yield from str(content).splitlines()

def get_widths(content: Iterable[Iterable[Any]]) -> list[int]:
    """Returns list of column widths"""
    widths: dict[int,int] = defaultdict(lambda:0)
    for row in content:
        for col, cell in enumerate(row):
            if widths[col] < (cell_length:= Content(cell).width):
                widths[col] = cell_length
    return list(widths.values())

class Content:
    def __init__(self, content: Any):
        self.text = str(content)

    @property
    def width(self) -> int:
        widths = self.text.splitlines()
        return len(max(widths, key=len)) if widths else 0

    @property
    def height(self) -> int:
        return str_height(self.text)

    @property
    def size(self) -> tuple[int,int]:
        return (self.height, self.width)

    def __str__(self) -> str:
        string = ""
        for line in self.text.splitlines():
            string += h_pad(line, self.width, align=0)
        return string

@dataclass(frozen=True)
class CellFormat:
    v_align: float = .5
    h_align: float = .5
    fill: str = " "

    def __post_init__(self) -> None:
        v_in = 0 <= self.v_align <= 1
        h_in = 0 <= self.h_align <= 1
        if not (v_in and h_in):
            raise ValueError("Values must be in the interval [0,1]")

@dataclass
class Cell:
    content: Content
    height: int
    width: int
    fmt: CellFormat = CellFormat()

    def print_range(self) -> range:
        start = round((self.height - self.content.height)*self.fmt.v_align)
        end = start+self.content.height
        return range(start,end)

    def __str__(self) -> str:
        string = ""
        content_iter = line_iter(self.content)

        for x in range(self.height):
            content = ""
            if x in self.print_range():
                content = next(content_iter)
            string += h_pad(content, self.width, self.fmt.h_align, self.fmt.fill)
        return string

class Divider:
    def __init__(self, chars: Iterable[str], positions: Iterable[int]):
        self.chars = cycle(chars)
        self.positions = positions


@dataclass
class Row:
    cells: list[Cell]
    divider: Divider

    def __str__(self) -> str:
        string = ""
        iters = [line_iter(cell) for cell in self.cells]
        for _ in range(self.cells[0].height):
            chars = next(self.divider.chars)
            string += chars.join(next(cell_line) for cell_line in iters) + "\n"
        return string

class TableFormat:
    def __init__(self, h_div: Divider = Divider("─", range(100)),
            v_div: Divider = Divider("│", range(100)), joint: str = "┼"):
        self.h_div = h_div
        self.v_div = v_div
        self.joint = joint

@dataclass
class Table:
    data: list[list[Any]]
    tab_fmt: TableFormat = TableFormat()

    @property
    def row_heights(self) -> list[int]:
        return [max([Content(text).height for text in row]) for row in self.data]

    @property
    def col_widths(self) -> list[int]:
        return get_widths(self.data)

    @property
    def rows(self) -> list[Row]:
        rows: list[Row] = []
        for height, row in zip_longest(self.row_heights, self.data):
            cell_list: list[Cell] = []
            for width, datum in zip_longest(self.col_widths, row, fillvalue=""):
                cell_list.append(Cell(Content(datum),height,width))
            rows.append(Row(cell_list, self.tab_fmt.v_div))
        return rows

    def __str__(self) -> str:
        string = ""
        for i, row in enumerate(self.rows):
            string += f"{row}"
            if i in self.tab_fmt.h_div.positions:
                divider = next(self.tab_fmt.h_div.chars)
                h_lines = [divider*width for width in self.col_widths]
                string += self.tab_fmt.joint.join(h_lines) + "\n"
        return string.removesuffix("\n")

