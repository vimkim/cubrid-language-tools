"""Values shared by completion and validation interfaces."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Span:
    start: int
    end: int

    def __post_init__(self):
        if type(self.start) is not int or type(self.end) is not int or not 0 <= self.start <= self.end:
            raise ValueError("span must be a half-open range of nonnegative code-point offsets")


@dataclass(frozen=True)
class CompletionItem:
    """One insertion value with a display label and descriptive metadata."""

    text: str
    detail: str = "keyword"

    @property
    def label(self) -> str:
        return self.text

    @property
    def kind(self) -> str:
        if self.text.startswith(';'):
            return 'command'
        if self.detail == 'result column':
            return 'column'
        if self.detail == 'parameter value':
            return 'value'
        words = self.detail.split()
        return words[1] if len(words) > 1 and words[0] == 'catalog' else words[0] if words else 'keyword'


@dataclass(frozen=True)
class CompletionResult:
    replacement: Span
    items: tuple[CompletionItem, ...]
    allowed: bool = True
    availability: str | None = None

    def __post_init__(self):
        object.__setattr__(self, 'items', tuple(self.items))


@dataclass(frozen=True)
class Relation:
    owner: str
    name: str
    kind: str
    columns: tuple[str, ...] = ()
    system: bool = False
    indexes: tuple[str, ...] = ()

    def __post_init__(self):
        object.__setattr__(self, 'columns', tuple(self.columns))
        object.__setattr__(self, 'indexes', tuple(self.indexes))


@dataclass(frozen=True)
class Schema:
    user: str = ""
    relations: tuple[Relation, ...] = ()
    users: tuple[str, ...] = ()
    database: str = ""

    def __post_init__(self):
        object.__setattr__(self, 'relations', tuple(self.relations))
        object.__setattr__(self, 'users', tuple(self.users))
