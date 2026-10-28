"""Compact maps of the original text; no Unicode or newline normalization."""

from array import array
from bisect import bisect_left, bisect_right


class DocumentMap:
    def __init__(self, text: str):
        self.text = text
        self._bytes = array("I", [0])
        self._utf16 = array("I", [0])
        self._starts = array("I", [0])
        byte_offset = utf16_offset = 0
        for offset, char in enumerate(text):
            scalar = ord(char)
            if 0xD800 <= scalar <= 0xDFFF:
                raise ValueError("document contains an invalid Unicode scalar")
            byte_offset += 1 if scalar < 0x80 else 2 if scalar < 0x800 else 3 if scalar < 0x10000 else 4
            utf16_offset += 2 if scalar > 0xFFFF else 1
            self._bytes.append(byte_offset)
            self._utf16.append(utf16_offset)
            if char == "\n":
                self._starts.append(offset + 1)

    @staticmethod
    def _integer(value):
        if type(value) is not int or value < 0:
            raise ValueError("position must be a nonnegative integer")

    def _line_end(self, line):
        if line + 1 == len(self._starts):
            return len(self.text)
        end = self._starts[line + 1] - 1
        return end - 1 if end and self.text[end - 1] == "\r" else end

    def to_byte(self, offset: int) -> int:
        self._integer(offset)
        if offset >= len(self._bytes):
            raise ValueError("code-point offset is outside the document")
        return self._bytes[offset]

    def from_byte(self, offset: int) -> int:
        self._integer(offset)
        index = bisect_left(self._bytes, offset)
        if index == len(self._bytes) or self._bytes[index] != offset:
            raise ValueError("byte offset is outside the document or inside UTF-8")
        return index

    def to_position(self, offset: int) -> tuple[int, int]:
        self.to_byte(offset)
        line = bisect_right(self._starts, offset) - 1
        if offset > self._line_end(line):
            raise ValueError("offset is inside CRLF")
        return line, self._utf16[offset] - self._utf16[self._starts[line]]

    def from_position(self, line: int, character: int) -> int:
        self._integer(line)
        self._integer(character)
        if line >= len(self._starts):
            raise ValueError("line is outside the document")
        start, end = self._starts[line], self._line_end(line)
        target = self._utf16[start] + character
        index = bisect_left(self._utf16, target, start, end + 1)
        if index > end or self._utf16[index] != target:
            raise ValueError("UTF-16 position is outside the line or inside a surrogate pair/CRLF")
        return index

    def human_location(self, offset: int) -> tuple[int, int]:
        self.to_byte(offset)
        line = bisect_right(self._starts, offset) - 1
        return line + 1, offset - self._starts[line] + 1
