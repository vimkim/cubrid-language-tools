"""Public completion contracts for callers without a terminal or catalog."""

from contextlib import ExitStack
from dataclasses import FrozenInstanceError
import os
import unittest
from unittest.mock import patch

from cubrid_language import CompletionItem, CompletionResult, Relation, Schema, Span, complete


PROFILE = 'cubrid-11.5.0.2704-cc94778'
SCHEMA = Schema('reader', (
  Relation('reader', 'code', 'CLASS', ('id', 'name'), indexes=('idx_name',)),
  Relation('PUBLIC', 'code', 'CLASS', ('public_name',)),
  Relation('OTHER', 'code', 'CLASS', ('other_name',), indexes=('idx_other',)),
  Relation('reader', 'odd name', 'VCLASS', ('odd column',)),
  Relation('DBA', 'db_class', 'VCLASS', ('class_name', 'owner_name'), True),
), ('DBA', 'PUBLIC', 'reader'), 'demo')


class CompletionCoreTest(unittest.TestCase):

  def test_cubrid_line_comments_and_escaped_strings_suppress_completion(self):
    for text in ('// SEL', '// 가😀 SEL', "SELECT 'x\\' SEL", "SELECT '가😀\\'\r\n;he"):
      with self.subTest(text=text):
        result = complete(text, len(text), PROFILE)
        self.assertFalse(result.allowed)
        self.assertEqual(result.items, ())
    for text in ('// comment\r\nSEL', "SELECT 'x\\\\';\r\nSEL"):
      self.assertEqual([item.text for item in complete(text, len(text), PROFILE).items], ['SELECT'])

  def test_mixed_document_completion_uses_current_command_line_and_original_spans(self):
    for marked, span, expected in (
      (';help\nSEL|tail', Span(6, 13), 'SELECT'),
      ('SELECT 1;\n;he|tail', Span(10, 17), ';help'),
      (';help\r\nSHOW TA|tail', Span(12, 18), 'TABLES'),
      ('// 가😀\r\n;help\r\nSEL|tail', Span(14, 21), 'SELECT'),
    ):
      with self.subTest(marked=marked):
        text, cursor = marked.replace('|', ''), marked.index('|')
        result = complete(text, cursor, PROFILE)
        self.assertEqual(result.replacement, span)
        self.assertIn(expected, [item.text for item in result.items])
        self.assertEqual(text[:span.start] + expected + text[span.end:],
                         text[:result.replacement.start] + expected + text[result.replacement.end:])
    for text in ("SELECT 'x\n;he", '/* comment\n;he', ";schema 'x\nSEL"):
      self.assertFalse(complete(text, len(text), PROFILE).allowed)
    for text in ('SELECT * FROM code\n;\nna', 'SELECT * FROM code;\nna'):
      self.assertNotIn('name', [item.text for item in complete(text, len(text), PROFILE, SCHEMA).items])
    self.assertIn(';help', [item.text for item in complete(';', 1, PROFILE).items])

  def test_completion_kind_handles_empty_and_incomplete_display_detail(self):
    for detail, expected in (('', 'keyword'), ('  ', 'keyword'), ('catalog', 'catalog'),
                             ('catalog table', 'table')):
      self.assertEqual(CompletionItem('name', detail).kind, expected)

  def test_offline_completion_returns_ordered_items_and_a_replacement_span(self):
    result = complete('selwrong;', 3, PROFILE)
    self.assertTrue(result.allowed)
    self.assertIs(type(result.replacement), Span)
    self.assertEqual((0, 8), (result.replacement.start, result.replacement.end))
    self.assertEqual([('SELECT', 'SELECT', 'keyword', 'keyword')],
                     [(item.text, item.label, item.kind, item.detail) for item in result.items])
    self.assertIsNone(result.availability)

  def test_out_of_document_cursors_cannot_produce_invalid_spans(self):
    for cursor in (-1, 4):
      with self.subTest(cursor=cursor), self.assertRaises(ValueError):
        complete('sel', cursor, PROFILE)

  def test_cursor_offsets_are_integers_including_at_document_boundaries(self):
    for cursor in (False, True, 1.5, '1', None):
      with self.subTest(cursor=cursor), self.assertRaises(TypeError):
        complete('sel', cursor, PROFILE)
    for text, cursor in (('', 0), ('sel', 0), ('sel', 3)):
      with self.subTest(text=text, cursor=cursor):
        result = complete(text, cursor, PROFILE)
        self.assertTrue(0 <= result.replacement.start <= result.replacement.end <= len(text))

  def test_korean_emoji_and_crlf_preserve_code_point_replacement_offsets(self):
    text = '/* 가😀 */\r\nselect * from cowrong;'
    result = complete(text, 26, PROFILE, SCHEMA)
    self.assertEqual((24, 31), (result.replacement.start, result.replacement.end))
    item = next(item for item in result.items if item.text == 'code')
    replaced = text[:result.replacement.start] + item.text + text[result.replacement.end:]
    self.assertEqual('/* 가😀 */\r\nselect * from code;', replaced)

  def test_unicode_identifier_edits_preserve_multiline_source(self):
    schema = Schema('사용자', (
      Relation('사용자', '고객', 'CLASS', ('이름',)),
      Relation('사용자', '😀 목록', 'CLASS'),
    ))
    cases = (
      ('-- 😀\r\nselect *\r\nfrom 고|잘못;', Span(21, 24), '고객',
       '-- 😀\r\nselect *\r\nfrom 고객;'),
      ('/* 😀 */\nselect * from [😀 |잘못];', Span(22, 28), '[😀 목록]',
       '/* 😀 */\nselect * from [😀 목록];'),
      ('select 고.이|잘못\r\nfrom 고객 고;', Span(9, 12), '이름',
       'select 고.이름\r\nfrom 고객 고;'),
    )
    for marked, span, insertion, expected in cases:
      with self.subTest(marked=marked):
        text = marked.replace('|', '')
        result = complete(text, marked.index('|'), PROFILE, schema)
        self.assertEqual(span, result.replacement)
        item = next(item for item in result.items if item.text == insertion)
        self.assertEqual(expected, text[:span.start] + item.text + text[span.end:])

  def test_incomplete_queries_quotes_aliases_and_shadowing_keep_their_results(self):
    cases = (
      ('select c.na|wrong from code c', ['name']),
      ('select * from [odd|wrong]', ['[odd name]']),
      ('select * from "odd|wrong"', ['"odd name"']),
      ('select * from `odd|wrong`', ['`odd name`']),
      ('select * from co|', ['code', 'OTHER.code', 'PUBLIC.code']),
      ('select x.ot| from other.code x', ['other_name']),
      ('select * from code where (na|', ['name']),
      ('select (select c.ow| from db_class c) from code c', ['owner_name']),
    )
    for marked, expected in cases:
      with self.subTest(marked=marked):
        result = complete(marked.replace('|', ''), marked.index('|'), PROFILE, SCHEMA)
        self.assertEqual(expected, [item.text for item in result.items])

  def test_expanded_schema_fields_drive_command_completion(self):
    cases = (
      ('SHOW INDEX HEADER OF other.code.idx', ['idx_other'], ['index']),
      ('SHOW GRANTS FOR re', ['reader'], ['user']),
      ('SHOW TABLES WHERE tab', ['tables_in_demo'], ['column']),
      ('select * from db_cl', ['db_class'], ['view']),
      (';connect re', ['reader'], ['user']),
      (';sc', [';schema'], ['command']),
      (';set lock_', ['lock_timeout='], ['parameter']),
      ("SET SYSTEM PARAMETERS 'lock_timeout=D", ['DEFAULT'], ['value']),
    )
    for text, names, kinds in cases:
      with self.subTest(text=text):
        result = complete(text, len(text), PROFILE, SCHEMA)
        self.assertEqual(names, [item.text for item in result.items])
        self.assertEqual(kinds, [item.kind for item in result.items])

  def test_unknown_schema_does_not_invent_relation_or_column_names(self):
    for marked in ('select * from co|', 'select c.na| from code c'):
      with self.subTest(marked=marked):
        result = complete(marked.replace('|', ''), marked.index('|'), PROFILE)
        self.assertEqual((), result.items)
    self.assertEqual(['SELECT'], [item.text for item in complete('sel', 3, PROFILE).items])

  def test_comments_and_strings_suppress_sql_completion(self):
    for marked in ("select 'co|wrong'", '-- co|', 'select /* co|', ';schema \'co|'):
      with self.subTest(marked=marked):
        result = complete(marked.replace('|', ''), marked.index('|'), PROFILE, SCHEMA)
        self.assertFalse(result.allowed)
        self.assertEqual((), result.items)
    text = '-- 가😀\r\nsel'
    self.assertTrue(complete(text, len(text), PROFILE).allowed)

  def test_results_and_schema_values_are_immutable(self):
    result = complete('sel', 3, PROFILE, SCHEMA)
    for value, field, replacement in (
      (result, 'allowed', False), (result.replacement, 'start', 1),
      (result.items[0], 'text', 'broken'), (SCHEMA, 'user', 'other'),
      (SCHEMA.relations[0], 'system', True),
    ):
      with self.subTest(field=field), self.assertRaises(FrozenInstanceError):
        setattr(value, field, replacement)
    self.assertIsInstance(result.items, tuple)
    self.assertEqual(('DBA', 'PUBLIC', 'reader'), SCHEMA.users)
    self.assertEqual('demo', SCHEMA.database)
    self.assertEqual(('idx_name',), SCHEMA.relations[0].indexes)

  def test_schema_values_snapshot_mutable_caller_collections(self):
    columns, indexes = ['name'], ['idx_name']
    relation = Relation('reader', 'code', 'CLASS', columns, indexes=indexes)
    relations, users = [relation], ['reader']
    schema = Schema('reader', relations, users, 'demo')
    columns.clear()
    indexes.clear()
    relations.clear()
    users.clear()
    self.assertEqual(('name',), relation.columns)
    self.assertEqual(('idx_name',), relation.indexes)
    self.assertEqual((relation,), schema.relations)
    self.assertEqual(('reader',), schema.users)
    result = complete('select c.na from code c', 11, PROFILE, schema)
    self.assertEqual(['name'], [item.text for item in result.items])

  def test_completion_result_snapshots_caller_items(self):
    items = [CompletionItem('SELECT')]
    result = CompletionResult(Span(0, 3), items)
    items.clear()
    self.assertEqual((CompletionItem('SELECT'),), result.items)

  def test_completion_is_deterministic_without_io_or_environment_access(self):
    cases = (
      ('select c.na from code c', 11, SCHEMA), (';sc', 3, SCHEMA),
      (';get lock_', 10, None), ("SET SYSTEM PARAMETERS 'lock_timeout=D", 37, None),
      ('SHOW TABLES WHERE tab', 21, SCHEMA),
    )
    # These are system boundaries, not completion internals.
    with ExitStack() as guards:
      for target in ('builtins.open', 'io.open', 'os.open', 'os.getenv',
                     'subprocess.Popen', 'socket.socket', 'os.isatty'):
        guards.enter_context(patch(target, side_effect=AssertionError('completion attempted I/O')))
      guards.enter_context(patch.object(type(os.environ), '__getitem__',
                                       side_effect=AssertionError('completion read the environment')))
      for text, cursor, schema in cases:
        with self.subTest(text=text):
          result = complete(text, cursor, PROFILE, schema)
          self.assertEqual(result, complete(text, cursor, PROFILE, schema))


if __name__ == '__main__':
  unittest.main()
