"""Values shared by completion and validation interfaces."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Span:
    start: int
    end: int

    def __post_init__(self):
        if type(self.start) is not int or type(self.end) is not int or not 0 <= self.start <= self.end:
            raise ValueError("span must be a half-open range of nonnegative code-point offsets")
