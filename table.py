from __future__ import annotations
from dataclasses import dataclass
from itertools import zip_longest
from collections import defaultdict
from collections.abc import Generator, Iterable
from typing import Any

def h_pad(text: str, width: int, align: float, fill: str = " ") -> str:
    """Aligns text to a proportion (align) of width.
    For example, setting align to 0,.5, or 1 would left, center, or right align the text."""
    padding = width - len(text)
    lpad = round(align*padding)
    rpad = padding - lpad
    return f"{lpad*fill}{text}{rpad*fill}\n"

def line_iter(content: Any) -> Generator[str, None, None]:
    """Takes a string and returns a generator of string lines."""
    yield from str(content).splitlines()

def iter_join(iter1: Iterable[str], iter2: Iterable[str]) -> str:
    """Like join, except the join string is also an iterable.
    If one iterable is longer than the other the remainder of the longer Iterable
    will be appended to the string.

    [In] : iter_join('abcdef',[1,2,3])
    [Out]: 'a1b2c3def'"""

    string = ""
    for x,y in zip_longest(iter1, iter2, fillvalue=""):
        string += f"{x}{y}"
    return string

class Content:
    """Class containing the content to be displayed in a table."""
    def __init__(self, content: Any):
        self.text = str(content)
        self.width = self.get_width()
        self.height = self.get_height()

    def get_width(self) -> int:
        """Calculates the line width(s) of a block of text, and returns the greatest width."""
        widths = self.text.splitlines()
        return len(max(widths, key=len)) if widths else 0

    def get_height(self) -> int:
        """Returns the height of a block of text by counting the newlines in the block"""
        return self.text.count("\n") + 1 if self.text else 0

    @property
    def size(self) -> tuple[int,int]:
        """Returns the height and width of a block of text as a tuple"""
        return (self.height, self.width)

    def __str__(self) -> str:
        """Returns the string representation of self.text, padding the end of each line
        with spaces so that each line is self.width characters long."""
        string = ""
        for line in self.text.splitlines():
            string += h_pad(line, self.width, align=0)
        return string

@dataclass(frozen=True)
class CellFormat:
    """Determines the vertical and horizontal positioning of a cell's
    content as well as the fill to be used to pad the content."""
    v_align: float = .5
    h_align: float = .5
    fill: str = " "

    def __post_init__(self) -> None:
        """Checks to make sure the align values are between 0 and 1 inclusive.
        Throws a ValueError in the case that they're not."""
        v_in = 0 <= self.v_align <= 1
        h_in = 0 <= self.h_align <= 1
        if not (v_in and h_in):
            raise ValueError("Values must be in the interval [0,1]")

@dataclass
class Cell:
    """Contains and formats Content to be used in a Table."""
    content: Content
    height: int
    width: int
    fmt: CellFormat = CellFormat()

    def print_range(self) -> range:
        """Returns a range of lines in which self.content should be printed.
        This range is determined by the v_align parameter in CellFormat."""
        start = round((self.height - self.content.height)*self.fmt.v_align)
        end = start+self.content.height
        return range(start,end)

    def __str__(self) -> str:
        """Returns a string of size height*width containing the Cell instance's content."""
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
    """Class to facilitate cell division.

    char - the character that represets the divider, common examples might be '-' or '|'.
    slices - despite being plural, a singular slice that describes where char should be
    present in the Divider. So slice(1,-1) would exclude the first and last dividers in
    a table, which might look something like this ab|c|d|e|fg if default is "".
    default - where char isn't present, default is. The default of default is a space.
    """
    char: str
    slices: slice = slice(None)
    default: str = " "

    def chars(self, length: int) -> list[str]:
        """Returns a list of chars of size 'length' that follow the Divider's specifications."""
        divs = [self.default for _ in range(length)]
        divs[self.slices] = self.char*len(divs[self.slices])
        return divs

@dataclass
class Row:
    """A list of Cells coupled with a Table's vertical Divider. This class is basically just
    here to make it slightly easier to pretty print in Table.
    """
    cells: list[Cell]
    v_div: Divider

    def __str__(self) -> str:
        """Joins the characters from the Divider and the strings from the Cell list."""
        string = ""
        iters = [line_iter(cell) for cell in self.cells]
        num_divs = len(self.cells)-1
        for _ in range(self.cells[0].height):
            chars = self.v_div.chars(num_divs)
            iterline = (next(line) for line in iters)
            string += iter_join(iterline,chars) + "\n"
        return string

@dataclass
class Joint:
    """
    When two Dividers meet, they form a Joint.
    """
    char: str
    hor: Divider
    ver: Divider

    def get_joints(self, height: int, width: int) -> list[list[str]]:
        """Returns a height*width list of list of joints and Divider chars."""
        hor_divs = self.hor.chars(height)
        ver_divs = self.ver.chars(width)
        return [[self.char_return((x,y)," ") for y in ver_divs] for x in hor_divs]

    def char_return(self, tup: tuple[str,str], none: str) -> str:
        """Looks for whether both dividers are in the tuple and returns a joint if that's the
        case. Otherwise the returned character will be the Divider char, or none."""
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
    """Format information which determines how the table will look"""
    j_char: str = "┼"
    h_div: Divider = Divider("─")
    v_div: Divider = Divider("│")

    def __post_init__(self) -> None:
        """the joint needs to be created based on the Dividers passed in, and this is the way
        you do that with a dataclass. Might just turn this into a regular class."""

        self.joint = Joint(self.j_char,self.h_div,self.v_div)

    def div_lines(self, widths: list[int], tab_length: int,) -> list[str]:
        """Creates the horizontal dividers for a table. Note that currently the
        vertical dividers are part of the Row class."""

        divisions: list[str]= []
        h_chars = iter(self.h_div.chars(tab_length-1))
        joints = self.joint.get_joints(tab_length-1,len(widths)-1)
        for j in joints:
            char = next(h_chars)
            lines = [char*w for w in widths]
            divisions.append(iter_join(lines,j)+"\n")
        return divisions

class Table:
    def __init__(self, data: Iterable[Iterable[Any]], tab_fmt: TableFormat = TableFormat()):
        """Throw in an Iterable of Iterables and spit out a pretty printed Table"""
        self.data = data
        self.tab_fmt = tab_fmt
        self.row_heights = self.get_row_heights()
        self.col_widths = self.get_col_widths()
        self.rows = self.get_rows()

    def get_row_heights(self) -> list[int]:
        """Determines the heights for each row"""
        return [max([Content(text).height for text in row]) for row in self.data]

    def get_col_widths(self) -> list[int]:
        """Returns list of column widths"""
        widths: dict[int,int] = defaultdict(lambda:0)
        for row in self.data:
            for col, cell in enumerate(row):
                if widths[col] < (cell_length:= Content(cell).width):
                    widths[col] = cell_length
        return list(widths.values())

    def row(self, row_index: int) -> list[Cell]:
        """A list of cells from the index specified."""
        height = self.row_heights[row_index]
        widths_data = zip(self.col_widths, self.contents[row_index])
        cell_list = [Cell(content, height, width) for width, content in widths_data]
        return cell_list

    def get_rows(self) -> list[Row]:
        """Returns all the rows in the table"""
        rows: list[Row] = []
        for height, row in zip(self.row_heights, self.data):
            cell_list: list[Cell] = []
            for width, datum in zip_longest(self.col_widths, row, fillvalue=""):
                cell_list.append(Cell(Content(datum),height,width))
            rows.append(Row(cell_list, self.tab_fmt.v_div))
        return rows

    def __str__(self) -> str:
        """Pretty print the contents of the Table"""
        string = ""
        widths = self.col_widths
        dividers = self.tab_fmt.div_lines(widths,len(self.rows))
        for row, divider in zip_longest(self.rows,dividers,fillvalue=""):
            string+= f"{row}{divider}"
        return string.removesuffix("\n")

