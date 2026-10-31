"""Shared tolerant tokenization and authoring eligibility."""

from dataclasses import dataclass

from .models import Span
from .scripts import classify


@dataclass(frozen=True)
class Token:
  text: str
  start: int
  end: int
  kind: str
  depth: int
  closed: bool = True

  @property
  def name(self) -> str:
    return unquote(self.text, self.closed)

  @property
  def keyword(self) -> str:
    return self.text.upper() if self.kind == "word" else ""


def unquote(value: str, closed: bool = True) -> str:
  if value and value[0] in '["`':
    closer = ']' if value[0] == '[' else value[0]
    return value[1:-1 if closed else None].replace(closer * 2, closer)
  return value


def tokenize(text: str) -> list[Token]:
  """Keep source spans and tolerate incomplete comments, strings, and names."""
  tokens = []
  index, depth = 0, 0
  while index < len(text):
    start = index
    character = text[index]
    if character.isspace():
      index += 1
      continue
    kind, closed = "symbol", True
    if text.startswith(('--', '//'), index):
      end = text.find('\n', index)
      index = len(text) if end < 0 else end
      kind, closed = "comment", end >= 0
    elif text.startswith('/*', index):
      end = text.find('*/', index + 2)
      index = len(text) if end < 0 else end + 2
      kind, closed = "comment", end >= 0
    elif character in "'\"`[":
      closer = ']' if character == '[' else character
      kind = "string" if character == "'" else "identifier"
      index += 1
      closed = False
      while index < len(text):
        if character == "'" and text[index] == '\\':
          index = min(len(text), index + 2)
          continue
        if text[index] == closer:
          index += 1
          if index < len(text) and text[index] == closer:
            index += 1
            continue
          closed = True
          break
        index += 1
    elif character.isalnum() or character in '_$':
      index += 1
      while index < len(text) and (text[index].isalnum() or text[index] in '_$'):
        index += 1
      kind = "word"
    else:
      index += 1
    if character == ')' and kind == "symbol":
      depth = max(0, depth - 1)
    tokens.append(Token(text[start:index], start, index, kind, depth, closed))
    if character == '(' and kind == "symbol":
      depth += 1
  return tokens


@dataclass(frozen=True)
class AuthoringPart:
  """Eligible document span and tokens relative to its start."""

  span: Span
  tokens: tuple[Token, ...]


def authoring_parts(text: str) -> tuple[AuthoringPart, ...]:
  parts = []
  for part in classify(text):
    if part.kind != 'sql':
      continue
    tokens = tokenize(text[part.span.start:part.span.end])
    visible = [token for token in tokens if token.kind != 'comment']
    statement_start = 0
    for index, token in enumerate(visible):
      if index == statement_start:
        header = [item.keyword for item in visible[index:index + 4]]
        if header[:2] == ['CREATE', 'TRIGGER'] or header[:4] == ['CREATE', 'OR', 'REPLACE', 'TRIGGER']:
          end = part.span.start + token.start
          if part.span.start < end:
            parts.append(AuthoringPart(Span(part.span.start, end),
                                       tuple(item for item in tokens if item.end <= token.start)))
          break
      if token.text == ';':
        statement_start = index + 1
    else:
      parts.append(AuthoringPart(part.span, tuple(tokens)))
  return tuple(parts)
