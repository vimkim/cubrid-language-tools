"""Pure classification of original CSQL batch text; commands are never run."""

from dataclasses import dataclass
import re

from .models import Span


@dataclass(frozen=True)
class ScriptPart:
    """A contiguous half-open source slice: sql, command, or unsupported."""

    kind: str
    span: Span
    lexical_error: bool = False


_COMMAND_RULES = (
    ('help', ()), ('exit', ()), ('commit', ()), ('rollback', ()),
    ('autocommit', ('on', 'off')), ('time', ('on', 'off')), ('line-output', ('on', 'off')),
)
_COMMAND = re.compile(
    r';(?:' + '|'.join(name + (r'[ \t]+(?:' + '|'.join(arguments) + ')' if arguments else '')
                       for name, arguments in _COMMAND_RULES) + r')[ \t]*',
    re.IGNORECASE | re.ASCII,
)


def classify(text: str) -> tuple[ScriptPart, ...]:
    """Return source-ordered slices without reading files or changing text."""
    parts = []
    start = index = statement_start = 0
    header = []
    opaque = lexical_error = False
    procedural = False
    while index < len(text):
        if not opaque and (index == 0 or text[index - 1] == '\n'):
            newline = text.find('\n', index)
            end = len(text) if newline < 0 else newline + 1
            body = text[index:end].removesuffix('\n').removesuffix('\r')
            candidate = body.lstrip(' \t')
            if candidate.startswith('!') or (candidate.startswith(';') and candidate.rstrip(' \t') != ';'):
                if header:
                    if start < statement_start:
                        parts.append(ScriptPart('sql', Span(start, statement_start)))
                    start = statement_start
                    opaque = True
                    index = end
                    continue
                if start < index:
                    parts.append(ScriptPart('sql', Span(start, index)))
                kind = 'command' if _COMMAND.fullmatch(body) else 'unsupported'
                parts.append(ScriptPart(kind, Span(index, end)))
                start = index = statement_start = end
                header = []
                continue
        if text.startswith(('--', '//'), index):
            newline = text.find('\n', index + 2)
            index = len(text) if newline < 0 else newline + 1
        elif text.startswith('/*', index):
            closing = text.find('*/', index + 2)
            lexical_error = closing < 0
            index = len(text) if closing < 0 else closing + 2
        elif text[index] in "'\"`[":
            if len(header) < 4:
                header.append('quoted')
            opening = text[index]
            closing = ']' if opening == '[' else opening
            index += 1
            closed = False
            while index < len(text):
                if opening == "'" and text[index] == '\\':
                    index = min(index + 2, len(text))
                elif text[index] == closing:
                    index += 1
                    if index < len(text) and text[index] == closing:
                        index += 1
                    else:
                        closed = True
                        break
                else:
                    index += 1
            lexical_error = not closed
        elif not opaque and (text[index].isalpha() or text[index] == '_'):
            end = index + 1
            while end < len(text) and (text[end].isalnum() or text[end] == '_'):
                end += 1
            if len(header) < 4:
                header.append(text[index:end].upper())
                procedure = (header in (['BEGIN'], ['DECLARE']) or
                             (header[0] == 'CREATE' and
                              (header[1:] in (['PROCEDURE'], ['FUNCTION'], ['PACKAGE']) or
                               header[1:3] == ['OR', 'REPLACE'] and len(header) == 4
                               and header[3] in ('PROCEDURE', 'FUNCTION', 'PACKAGE'))))
                if procedure:
                    if start < statement_start:
                        parts.append(ScriptPart('sql', Span(start, statement_start)))
                    start = statement_start
                    opaque = procedural = True
            index = end
        else:
            if not opaque and text[index] == ';':
                statement_start = index + 1
                header = []
            elif not opaque and not text[index].isspace() and len(header) < 4:
                header.append('punctuation')
            index += 1
    if start < len(text):
        parts.append(ScriptPart('unsupported' if opaque else 'sql', Span(start, len(text)),
                                lexical_error and (not opaque or procedural)))
    return tuple(parts)
