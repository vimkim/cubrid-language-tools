import re

from ._source import authoring_parts
from .show_hint_inventory import HINTS as HINT_PAIRS, SHOW_FIRST as SHOW_WORDS, SHOW_PRODUCTIONS
from .validation.models import Diagnostic, PROFILE, Span

HINTS = frozenset(name for name, _ in HINT_PAIRS)
SHOW_FIRST = frozenset(SHOW_WORDS)
HINT_START = ('/*+', '--+', '//+')
def show_second_words():
    rules = dict(SHOW_PRODUCTIONS)

    def expand(symbols, words):
        if len(words) == 3 or not symbols:
            return (words,)
        symbol, rest = symbols[0], symbols[1:]
        if symbol in rules:
            return tuple(result for production in rules[symbol]
                         for result in expand(production.split() + rest, words))
        if symbol.isupper() or symbol == 'For':
            return expand(rest, (*words, symbol.upper().removesuffix('_')))
        return (words,)

    prefixes = tuple(prefix for production in rules['show_stmt']
                     if production.startswith('SHOW ')
                     for prefix in expand(production.split(), ()))
    unconstrained = {prefix[1] for prefix in prefixes if len(prefix) == 2}
    return {first: frozenset(prefix[2] for prefix in prefixes
                             if len(prefix) == 3 and prefix[1] == first)
            for first in SHOW_FIRST - unconstrained}


SHOW_SECOND = show_second_words()


def authoring_diagnostics(text, profile, script_mode='sql'):
    """Return exact, warning-only findings without starting a native worker."""
    if not isinstance(text, str) or not isinstance(profile, str) or script_mode not in ('sql', 'csql'):
        raise ValueError('expected Unicode text, profile, and sql or csql mode')
    try:
        encoded = text.encode('utf-8', errors='strict')
        profile.encode('utf-8', errors='strict')
    except UnicodeError as error:
        raise ValueError('input must contain valid Unicode scalars') from error
    if not profile or '\0' in profile or b'\0' in encoded or len(encoded) > 8 * 1024 * 1024:
        raise ValueError('invalid profile or document')
    if profile != PROFILE:
        return ()
    findings = []
    for part in authoring_parts(text):
        span = part.span
        tokens = part.tokens
        statement = []
        for token in tokens:
            start, end = span.start + token.start, span.start + token.end
            if token.kind == 'comment' and token.text.startswith(HINT_START):
                closed = token.closed if token.text.startswith('/*') else token.end < span.end - span.start
                if closed:
                    if token.text.startswith(('--', '//')) and token.text.endswith('\r'):
                        end -= 1
                    body_end = len(token.text) - (2 if token.text.startswith('/*') else 0)
                    body = token.text[3:body_end]
                    index = 1 if body.startswith('+') else 0
                    while index < len(body):
                        whitespace = re.match(r'\s*', body[index:])
                        index += whitespace.end()
                        if index == len(body):
                            break
                        match = re.match(r'[A-Za-z_][A-Za-z_0-9]*', body[index:])
                        if match is None:
                            break
                        name = match.group()
                        name_start = index
                        index += len(name)
                        if index < len(body) and body[index] == '(':
                            depth, cursor, quote, nested = 1, index + 1, '', False
                            while cursor < len(body) and depth:
                                char = body[cursor]
                                if quote:
                                    if char == '\\' and cursor + 1 < len(body) and body[cursor + 1] == quote:
                                        cursor += 1
                                    elif char == quote:
                                        quote = ''
                                elif char in '"`[':
                                    quote = ']' if char == '[' else char
                                elif char == '(':
                                    depth += 1
                                    nested = True
                                elif char == ')':
                                    depth -= 1
                                cursor += 1
                            if name and name.upper() not in HINTS:
                                offset = start + 3 + name_start
                                findings.append(Diagnostic('CUBRID-A1001', 'warning', 'Unknown optimizer hint: ' + name,
                                                           Span(offset, offset + len(name)), 'token', 'authoring'))
                            if depth or quote:
                                findings.append(Diagnostic('CUBRID-A1002', 'warning', 'Unterminated optimizer hint arguments',
                                                           Span(start + 3 + index, start + 3 + len(body.rstrip())), 'exact', 'authoring'))
                                break
                            if nested and name.upper() in HINTS:
                                findings.append(Diagnostic('CUBRID-A1002', 'warning', 'Nested optimizer hint arguments are invalid',
                                                           Span(start + 3 + index, start + 3 + cursor), 'exact', 'authoring'))
                            index = cursor
                            name = ''
                        if index < len(body) and not body[index].isspace():
                            break
                        if name and name.upper() not in HINTS:
                            offset = start + 3 + name_start
                            findings.append(Diagnostic('CUBRID-A1001', 'warning', 'Unknown optimizer hint: ' + name,
                                                       Span(offset, offset + len(name)), 'token', 'authoring'))
                    if (len(statement) >= 2 and statement[-2].keyword == 'SELECT'
                            and statement[-1].keyword in ('ALL', 'DISTINCT', 'DISTINCTROW')):
                        findings.append(Diagnostic('CUBRID-A1004', 'warning', 'Optimizer hints belong before SELECT modifiers',
                                                   Span(start, end), 'exact', 'authoring'))
            elif token.kind != 'comment':
                statement.append(token)
                if token.text == ';':
                    words = [t for t in statement if t.kind == 'word']
                    if (len(words) >= 2 and statement[:2] == words[:2] and words[0].keyword == 'SHOW'
                            and words[1].keyword not in SHOW_FIRST):
                        name = words[1]
                        findings.append(Diagnostic('CUBRID-A1003', 'warning', 'Unknown SHOW form: ' + name.text,
                                                   Span(span.start + name.start, span.start + name.end), 'token', 'authoring'))
                    elif (len(statement) >= 3 and statement[0].keyword == 'SHOW'
                          and statement[1].keyword in SHOW_SECOND
                          and (statement[2].text == ';' or statement[2].kind == 'word'
                               and statement[2].keyword not in SHOW_SECOND[statement[1].keyword])):
                        name = statement[2] if statement[2].text != ';' else statement[1]
                        findings.append(Diagnostic('CUBRID-A1003', 'warning', 'Malformed SHOW form',
                                                   Span(span.start + name.start, span.start + name.end), 'token', 'authoring'))
                    statement = []
    return tuple(findings)
