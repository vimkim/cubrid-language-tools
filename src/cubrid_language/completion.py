"""Pure tolerant completion, independent of terminal and catalog lifecycles."""

from __future__ import annotations

from dataclasses import dataclass
import re

from .completion_data import PARAMETERS
from .models import CompletionItem, CompletionResult, Relation, Schema, Span
from .syntax import SESSION_COMMANDS, contexts


KEYWORDS = tuple("""
ALTER AND AS ASC BY CALL CASE COMMIT CREATE DELETE DESC DISTINCT DROP ELSE END
DESCRIBE EXPLAIN GET EXISTS FROM GROUP HAVING IN INSERT INTO IS JOIN LEFT LIMIT
NOT NULL ON OR ORDER
RIGHT ROLLBACK SELECT SET SHOW STATISTICS TABLE THEN UNION UPDATE VALUES VIEW WHEN WHERE
""".split())


# CUBRID 11.5 reserved-word snapshot from src/parser/keyword.c and the manual.
# Keep quoting separate from the smaller list offered as keyword suggestions.
RESERVED = frozenset("""
ABSOLUTE ACCESS ACTION ADD ADD_MONTHS AFTER ALL ALLOCATE ALTER AND ANTI ANY ARE AS ASC
ASSERTION ASYNC AT ATTACH ATTRIBUTE AVG BEFORE BEGIN BETWEEN BIGINT BINARY BIT BIT_LENGTH
BLOB BOOLEAN BOTH BREADTH BY CALL CASCADE CASCADED CASE CAST CATALOG CHANGE CHAR CHARACTER
CHECK CLASS CLASSES CLOB COALESCE COLLATE COLLATION COLUMN COMMIT CONNECT CONNECTION
CONNECT_BY_ISCYCLE CONNECT_BY_ISLEAF CONNECT_BY_ROOT CONSTRAINT CONSTRAINTS CONTINUE
CONVERT CORRESPONDING COUNT CREATE CROSS CURRENT CURRENT_DATE CURRENT_DATETIME
CURRENT_TIME CURRENT_TIMESTAMP CURRENT_USER CURSOR CYCLE DATA DATABASE DATA_TYPE
DATA_TYPE___ DATE DATETIME DATETIMELTZ DATETIMETZ DAY DAY_HOUR DAY_MILLISECOND DAY_MINUTE
DAY_SECOND DEALLOCATE DEC DECIMAL DECLARE DEFAULT DEFERRABLE DEFERRED DELETE DEPTH DESC
DESCRIBE DESCRIPTOR DIAGNOSTICS DIFFERENCE DISCONNECT DISTINCT DISTINCTROW DIV DO DOMAIN
DOUBLE DROP DUPLICATE EACH ELSE ELSEIF END ENUM EQUALS ESCAPE EVALUATE EXCEPT EXCEPTION
EXEC EXECUTE EXISTS EXTERNAL EXTRACT FALSE FETCH FILE FIRST FLOAT FOR FOREIGN FOUND FROM
FULL FUNCTION GENERAL GET GLOBAL GO GOTO GRANT GROUP HAVING HOUR HOUR_MILLISECOND
HOUR_MINUTE HOUR_SECOND IDENTITY IF IGNORE IMMEDIATE IN INDEX INDICATOR INHERIT INITIALLY
INNER INOUT INPUT INSERT INT INTEGER INTERSECT INTERSECTION INTERVAL INTO IS ISOLATION
JOIN JSON KEY LANGUAGE LAST LEADING LEAVE LEFT LESS LEVEL LIKE LIMIT LIST LOCAL LOCALTIME
LOCALTIMESTAMP LOCAL_TRANSACTION_ID LOOP LOWER MATCH MAX MEDIUMINT MERGE METHOD
MILLISECOND MIN MINUTE MINUTE_MILLISECOND MINUTE_SECOND MOD MODIFY MODULE MONETARY MONTH
MULTISET MULTISET_OF NA NAMES NATIONAL NATURAL NCHAR NEXT NO NONE NOT NULL NULLIF NUMERIC
OBJECT OCTET_LENGTH OF OFF ON ONLY OPTIMIZATION OPTION OR ORDER OUT OUTER OUTPUT OVERLAPS
PARAMETERS PARTIAL PARTITION POSITION PRECISION PREPARE PRESERVE PRIMARY PRIOR PRIVILEGES
PROCEDURE QUERY READ REAL RECURSIVE REF REFERENCES REFERENCING RELATIVE RENAME REPLACE
RESIGNAL RESTRICT RETURN RETURNS REVOKE RIGHT ROLE ROLLBACK ROLLUP ROUTINE ROW ROWNUM ROWS
SAVEPOINT SCHEMA SCOPE SCOPE___ SCROLL SEARCH SECOND SECOND_MILLISECOND SECTION SELECT
SEMI SENSITIVE SEQUENCE SEQUENCE_OF SERIALIZABLE SESSION SESSION_USER SET SETEQ SETNEQ
SET_OF SHARED SHORT SIBLINGS SIMILAR SIZE SMALLINT SOME SQL SQLCODE SQLERROR SQLEXCEPTION
SQLSTATE SQLWARNING STATISTICS STRING SUBCLASS SUBSET SUBSETEQ SUBSTRING SUM SUPERCLASS
SUPERSET SUPERSETEQ SYSDATE SYSDATETIME SYSTEM_USER SYSTIME SYSTIMESTAMP
SYS_CONNECT_BY_PATH SYS_DATE SYS_DATETIME SYS_REFCURSOR SYS_TIME SYS_TIMESTAMP TABLE
TEMPORARY THEN TIME TIMESTAMP TIMESTAMPLTZ TIMESTAMPTZ TIMEZONE_HOUR TIMEZONE_MINUTE
TINYINT TO TRAILING TRANSACTION TRANSLATE TRANSLATION TRIGGER TRIM TRUE TRUNCATE UNDER
UNION UNIQUE UNKNOWN UPDATE UPPER USAGE USE USER USING UTIME VACUUM VALUE VALUES VARCHAR
VARIABLE VARYING VCLASS VIEW WHEN WHENEVER WHERE WHILE WITH WITHOUT WORK WRITE XOR YEAR
YEAR_MONTH ZONE
""".split())


@dataclass(frozen=True)
class _Suggestions:
  start: int
  end: int
  candidates: tuple[CompletionItem, ...]
  allowed: bool = True


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


def identifier(value: str, quote: str = "") -> str:
  if not quote and re.fullmatch(r"[^\W\d]\w*", value, re.UNICODE) and value.upper() not in RESERVED:
    return value
  quote = quote or '['
  closer = ']' if quote == '[' else quote
  return quote + value.replace(closer, closer * 2) + closer


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


def statement_scope(tokens: list[Token], cursor: int) -> list[Token]:
  """Keep expression parentheses in scope, but exclude other SELECT scopes."""
  visible = [t for t in tokens if t.kind != 'comment']
  stack = []
  ranges = []
  end = tokens[-1].end if tokens else cursor
  for index, token in enumerate(visible):
    if token.kind != 'symbol':
      continue
    if token.text == '(':
      subquery = index + 1 < len(visible) and visible[index + 1].keyword in ('SELECT', 'WITH')
      stack.append((token.end, subquery))
    elif token.text == ')' and stack:
      opened, subquery = stack.pop()
      if subquery:
        ranges.append((opened, token.start))
  ranges.extend((opened, end + 1) for opened, subquery in stack if subquery)
  containing = [(left, right) for left, right in ranges if left <= cursor <= right]
  start, end = max(containing, default=(0, end + 1))
  nested = [(left, right) for left, right in ranges if start < left and right <= end]
  scoped = [t for t in visible if start <= t.start < end and not any(left <= t.start < right for left, right in nested)]
  for token in scoped:
    if token.kind == 'symbol' and token.text == ';':
      if token.start < cursor:
        start = token.end
      else:
        end = token.start
        break
  return [t for t in scoped if start <= t.start < end]


def table_position(tokens: list[Token]) -> bool:
  if not tokens:
    return False
  if tokens[-1].keyword in ("FROM", "JOIN", "UPDATE", "INTO"):
    return True
  if tokens[-1].text == ',':
    clauses = [t.keyword for t in tokens if t.keyword in ("SELECT", "FROM", "WHERE", "ON", "SET", "ORDER", "GROUP")]
    return bool(clauses and clauses[-1] == "FROM")
  return False


def referenced_relations(tokens: list[Token], schema: Schema) -> list[tuple[str, Relation]]:
  found = []
  for index, token in enumerate(tokens):
    if not table_position(tokens[:index + 1]):
      continue
    index += 1
    if index >= len(tokens) or tokens[index].kind not in ("word", "identifier"):
      continue
    owner, name = "", tokens[index].name
    index += 1
    if index + 1 < len(tokens) and tokens[index].text == '.':
      owner, name = name, tokens[index + 1].name
      index += 2
    matches = matching_relations(schema, (owner, name) if owner else (name,))
    if len(matches) != 1:
      continue
    alias = name
    if index < len(tokens) and tokens[index].keyword == "AS":
      index += 1
    if index < len(tokens) and tokens[index].kind in ("word", "identifier") and tokens[index].keyword not in RESERVED:
      alias = tokens[index].name
    found.append((alias, matches[0]))
  return found


def unqualified_relation(relation: Relation, schema: Schema) -> bool:
  return relation.owner.casefold() in (schema.user.casefold(), 'public') or (
    relation.system and relation.owner.casefold() == 'dba' and
    (relation.name.casefold().startswith(('db_', '_db')) or relation.name.casefold() == 'dual')
  )


def matching_relations(schema: Schema, names: tuple[str, ...]) -> list[Relation]:
  if not names:
    return []
  found = [r for r in schema.relations if r.name.casefold() == names[-1].casefold() and (
    r.owner.casefold() == names[0].casefold() if len(names) == 2 else unqualified_relation(r, schema)
  )]
  own = [r for r in found if r.owner.casefold() == schema.user.casefold()]
  return own or found


def relation_candidates(schema: Schema, prefix: str, quote: str, target: str = 'relation',
                        qualifier: tuple[str, ...] = ()) -> list[CompletionItem]:
  candidates = []
  if target == 'index' and qualifier:
    for relation in matching_relations(schema, qualifier):
      candidates.extend(CompletionItem(identifier(name, quote), 'index ' + relation.name)
                        for name in relation.indexes if name.casefold().startswith(prefix))
    # A single component can also be an owner before an unfinished table name.
    if len(qualifier) > 1:
      return candidates
  if len(qualifier) > 1:
    return candidates
  for relation in schema.relations:
    if not relation.name.casefold().startswith(prefix):
      continue
    if qualifier and relation.owner.casefold() != qualifier[0].casefold():
      continue
    if target == 'view' and relation.kind != 'VCLASS' or target in ('table', 'tables', 'index') and relation.kind != 'CLASS':
      continue
    if relation.system and not qualifier and not prefix.startswith(('db_', '_db')):
      continue
    own = unqualified_relation(relation, schema)
    if relation.owner.casefold() != schema.user.casefold():
      own = own and not any(r.owner.casefold() == schema.user.casefold() and r.name.casefold() == relation.name.casefold()
                            for r in schema.relations)
    rendered = identifier(relation.name, quote)
    if not qualifier and not own:
      rendered = identifier(relation.owner) + '.' + rendered
    if target == 'index':
      rendered += '.'
    kind = 'view' if relation.kind == 'VCLASS' else 'table'
    candidates.append(CompletionItem(rendered, ('catalog ' if relation.system else '') + kind + ' ' + relation.owner))
  return candidates


def parameter_suggestions(text: str, cursor: int, start: int, end: int, setting: bool,
                          sql: bool = False) -> _Suggestions:
  segment = text[start:cursor]
  if sql:
    start += segment.rfind(';') + 1
    segment = text[start:cursor]
  match = re.fullmatch(r'\s*(\w*)(?:\s*=\s*(\w*))?', segment)
  if match is None:
    return _Suggestions(cursor, cursor, ())
  name, value = match.groups()
  if value is not None and not setting:
    return _Suggestions(cursor, cursor, ())
  group = 2 if value is not None else 1
  replace_start = start + match.start(group)
  suffix = re.match(r'\w*', text[cursor:end])
  replace_end = cursor + len(suffix[0])
  if value is None:
    append_equals = setting and not text[replace_end:end].lstrip().startswith('=')
    candidates = tuple(CompletionItem(key + ('=' if append_equals else ''),
                                 'parameter ' + kind + (' (DBA)' if dba else ''))
                       for key, (kind, dynamic, dba) in PARAMETERS.items()
                       if key.startswith(name.casefold()) and (not setting or dynamic))
  else:
    kind = PARAMETERS.get(name.casefold(), ('', False, False))[0]
    values = ['yes', 'no'] if kind == 'bool' else []
    if sql and name.casefold() != 'call_stack_dump_activation_list':
      values.append('DEFAULT')
    candidates = tuple(CompletionItem(word, 'parameter value') for word in values if word.casefold().startswith(value.casefold()))
  return _Suggestions(replace_start, replace_end, candidates)


def session_suggestions(text: str, cursor: int, schema: Schema) -> _Suggestions:
  command = re.match(r'\s*;([.\w-]*)', text)
  assert command is not None
  if cursor <= command.end():
    prefix = text[command.start(1):cursor].casefold()
    return _Suggestions(command.start(1) - 1, command.end(), tuple(
      CompletionItem(';' + name, detail) for name, detail in sorted(SESSION_COMMANDS.items()) if name.startswith(prefix)))
  name = command[1].casefold()
  matches = [key for key in SESSION_COMMANDS if key.startswith(name)]
  if name not in SESSION_COMMANDS:
    if len(matches) != 1:
      return _Suggestions(cursor, cursor, ())
    name = matches[0]
  if name in ('get', 'set'):
    return parameter_suggestions(text, cursor, command.end(), len(text), name == 'set')
  tokens = [Token(';' + name, command.start(), command.end(), 'word', 0)]
  tokens += [Token(t.text, t.start + command.end(), t.end + command.end(), t.kind, t.depth, t.closed)
             for t in tokenize(text[command.end():])]
  return _complete_tokens(text, cursor, schema, tokens, session=True)


def _suggest(text: str, cursor: int, schema: Schema) -> _Suggestions:
  tokens = tokenize(text)
  commands = {}
  line_start = text.rfind('\n', 0, cursor) + 1
  for token in tokens:
    if token.kind != 'symbol' or token.text != ';':
      continue
    start = text.rfind('\n', 0, token.start) + 1
    if text[start:token.start].strip():
      continue
    end = text.find('\n', token.end)
    end = len(text) if end < 0 else end
    if text[start:end].strip() == ';' and start != line_start:
      continue
    commands[start] = end
  if line_start in commands:
    result = session_suggestions(text[line_start:commands[line_start]], cursor - line_start, schema)
    return _Suggestions(result.start + line_start, result.end + line_start, result.candidates, result.allowed)
  tokens = [token for token in tokens if not any(start <= token.start < end and token.end <= end
                                                for start, end in commands.items())]
  return _complete_tokens(text, cursor, schema, tokens)


def _complete_tokens(text: str, cursor: int, schema: Schema, tokens: list[Token], session: bool = False) -> _Suggestions:
  current = next((t for t in tokens if t.start < cursor <= t.end and (
    t.kind in ('word', 'identifier') or t.kind in ('comment', 'string') and (
      cursor < t.end or not t.closed or t.text.startswith(('--', '//'))
    )
  )), None)
  if current and current.kind in ('comment', 'string'):
    preceding = [t.keyword for t in statement_scope(tokens, cursor) if t.end <= current.start]
    if current.kind == 'string' and preceding == ['SET', 'SYSTEM', 'PARAMETERS']:
      end = current.end - (1 if current.closed else 0)
      return parameter_suggestions(text, cursor, current.start + 1, end, True, sql=True)
    return _Suggestions(cursor, cursor, (), allowed=False)
  start, end = (current.start, current.end) if current else (cursor, cursor)
  quote = text[start:start + 1] if current and current.kind == 'identifier' else ''
  prefix = unquote(text[start:cursor], bool(current and current.closed and cursor == current.end)).casefold()
  scoped = [t for t in tokens if t.kind != 'comment'] if session else statement_scope(tokens, cursor)
  before = [t for t in scoped if t.end <= start]
  command_contexts = contexts(before)
  candidates = []
  if command_contexts is not None:
    for context in command_contexts:
      if not quote:
        candidates.extend(CompletionItem(word, context.detail) for word in context.words if word.casefold().startswith(prefix))
      if context.target in ('relation', 'table', 'tables', 'view', 'index'):
        candidates.extend(relation_candidates(schema, prefix, quote, context.target, context.qualifier))
      elif context.target == 'user' and not context.qualifier:
        candidates.extend(CompletionItem(identifier(user, quote), 'user') for user in schema.users if user.casefold().startswith(prefix))
      if not before or before[-1].text != '.':
        for field in context.fields:
          if field == '<tables>':
            field = 'tables_in_' + schema.database if schema.database else ''
          if field and field.casefold().startswith(prefix):
            candidates.append(CompletionItem(identifier(field, quote), 'result column'))
    return ordered_suggestions(start, end, candidates)
  qualifier = ()
  if len(before) >= 2 and before[-1].text == '.':
    qualifier = (before[-2].name,)
    before = before[:-2]
  if table_position(before) or not before and prefix.startswith(('db_', '_db')):
    candidates.extend(relation_candidates(schema, prefix, quote, qualifier=qualifier))
    if len(before) == 1 and before[0].keyword == 'UPDATE' and not qualifier and not quote and 'statistics'.startswith(prefix):
      candidates.append(CompletionItem('STATISTICS'))
  else:
    references = referenced_relations(scoped, schema)
    for alias, relation in references:
      if qualifier and alias.casefold() != qualifier[0].casefold():
        continue
      for column in relation.columns:
        if column.casefold().startswith(prefix):
          rendered = identifier(column, quote)
          if not qualifier and len(references) > 1:
            rendered = identifier(alias) + '.' + rendered
          candidates.append(CompletionItem(rendered, 'column ' + alias))
    if not qualifier and not quote:
      candidates.extend(CompletionItem(word) for word in KEYWORDS if word.casefold().startswith(prefix))
  return ordered_suggestions(start, end, candidates)


def ordered_suggestions(start: int, end: int, candidates: list[CompletionItem]) -> _Suggestions:
  unique = {candidate.text: candidate for candidate in candidates}
  ordered = tuple(sorted(unique.values(), key=lambda c: (c.detail.startswith('keyword'), c.text.casefold())))
  return _Suggestions(start, end, ordered)


def complete(text: str, cursor: int, profile: str, schema: Schema | None = None) -> CompletionResult:
  """Suggest edits without I/O, including for unfinished SQL.

  ``profile`` is explicit caller context for future dialect-specific completion.
  The current tolerant vocabulary is the integrated terminal baseline. These
  suggestions do not establish syntax validity or qualified profile coverage.
  """
  if not isinstance(cursor, int) or isinstance(cursor, bool):
    raise TypeError('completion cursor must be an integer code-point offset')
  if not 0 <= cursor <= len(text):
    raise ValueError('completion cursor must be within the document')
  result = _suggest(text, cursor, schema if schema is not None else Schema())
  return CompletionResult(Span(result.start, result.end), result.candidates,
                          result.allowed)
