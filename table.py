#standard functional
from __future__ import annotations
from dataclasses import dataclass
from itertools import zip_longest
from collections import defaultdict

#typing
from typing import Any
from collections.abc import Generator, Iterable

def h_pad(text: str, width: int, align: float, fill: str = " ") -> str:
    padding = width - len(text)
    lpad = round(align*padding)
    rpad = padding - lpad
    return f"{lpad*fill}{text}{rpad*fill}\n"

def line_iter(content: Any) -> Generator[str, None, None]:
    yield from str(content).splitlines()

def iter_join(iter1: Iterable[str], iter2: Iterable[str]) -> str:
    string = ""
    for x,y in zip_longest(iter1, iter2, fillvalue=""):
        string += f"{x}{y}"
    return string + "\n"

class Content:
    def __init__(self, content: Any):
        self.text = str(content)
        self.width = self.get_width()
        self.height = self.get_height()

    def get_width(self) -> int:
        widths = self.text.splitlines()
        return len(max(widths, key=len)) if widths else 0

    def get_height(self) -> int:
        return self.text.count("\n") + 1 if self.text else 0

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

    def chars(self, length: int) -> list[str]:
        divs = [self.default for _ in range(length)]
        divs[self.slices] = self.char*len(divs[self.slices])
        return divs

@dataclass
class Row:
    cells: list[Cell]
    v_div: Divider

    def __str__(self) -> str:
        string = ""
        iters = [line_iter(cell) for cell in self.cells]
        num_divs = len(self.cells)-1
        for _ in range(self.cells[0].height):
            chars = self.v_div.chars(num_divs)
            iterline = (next(line) for line in iters)
            string += iter_join(iterline,chars)
        return string

@dataclass
class Joint:
    char: str
    hor: Divider
    ver: Divider

    def get_joints(self, height: int, width: int) -> list[list[str]]:
        hor_divs = self.hor.chars(height)
        ver_divs = self.ver.chars(width)
        return [[self.char_return((x,y)," ") for y in ver_divs] for x in hor_divs]

    def char_return(self, tup: tuple[str,str], none: str) -> str:
        if self.hor.char in tup and self.ver.char in tup:
            return self.char
        elif self.hor.char in tup:
            return self.hor.char
        elif self.ver.char in tup:
            return self.ver.char
        else:
            return none

@dataclass
class TableFormat:
    j_char: str = "┼"
    h_div: Divider = Divider("─")
    v_div: Divider = Divider("│")

    def __post_init__(self) -> None:
        self.joint = Joint(self.j_char,self.h_div,self.v_div)

    def div_lines(self, widths: list[int], tab_length: int,) -> list[str]:
        divisions: list[str]= []
        h_chars = iter(self.h_div.chars(tab_length-1))
        joints = self.joint.get_joints(tab_length-1,len(widths)-1)
        for j in joints:
            char = next(h_chars)
            lines = [char*w for w in widths]
            divisions.append(iter_join(lines,j))
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
        """Returns list of column widths"""
        widths: dict[int,int] = defaultdict(lambda:0)
        for row in self.data:
            for col, cell in enumerate(row):
                if widths[col] < (cell_length:= Content(cell).width):
                    widths[col] = cell_length
        return list(widths.values())

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

