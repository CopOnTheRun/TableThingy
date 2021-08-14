#standard functional
from __future__ import annotations
from dataclasses import dataclass
from itertools import zip_longest
from collections import defaultdict

#typing
from typing import Any
from collections.abc import Generator, Iterable, Iterator

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

def iter_join(iter1: Iterable[str], iter2: Iterable[str]):
    string = ""
    for x,y in zip_longest(iter1, iter2, fillvalue=""):
        string += f"{x}{y}"
    return string

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

@dataclass(frozen=True)
class Divider:
    char: str
    slices: slice = slice(None)
    default: str = " "

    def chars(self, length: int) -> Iterator[str]:
        divs = [self.default for _ in range(length)]
        divs[self.slices] = self.char*len(divs[self.slices])
        yield from divs

@dataclass
class Row:
    cells: list[Cell]
    v_div: Divider

    def __str__(self) -> str:
        string = ""
        iters = [line_iter(cell) for cell in self.cells]
        for _ in range(self.cells[0].height):
            chars = self.v_div.chars(1)
            string += next(chars).join(next(cell_line) for cell_line in iters) + "\n"
        return string

@dataclass
class TableFormat:
    h_div: Divider = Divider("─")
    v_div: Divider = Divider("│")
    joint: Divider = Divider("┼")

    def div_lines(self, widths: list[int], tab_length: int,) -> str:
        divisions = []
        h_chars = self.h_div.chars(tab_length)
        joints = self.joint.chars(tab_length)
        for _ in range(tab_length-1):
            char = next(h_chars)
            lines = [char*w for w in widths]
            joint = next(joints)
            divisions.append(joint.join(lines)+'\n')
        return divisions


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
        widths = self.col_widths
        dividers = self.tab_fmt.div_lines(widths,len(self.rows))
        for row, divider in zip_longest(self.rows,dividers,fillvalue=""):
            string+= f"{row}{divider}"
        return string.removesuffix("\n")

