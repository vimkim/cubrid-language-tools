"""Source-preserving batch classification through its public interface."""

import unittest

from cubrid_language.models import Span
from cubrid_language.scripts import classify


class ScriptTests(unittest.TestCase):
    def test_exact_commands_and_adjacent_sql_keep_original_codepoint_spans(self):
        text = ";HeLp\r\nSELECT '가😀;';\r\n;autocommit OFF\r\n;exit"
        parts = classify(text)
        self.assertEqual([(p.kind, p.span) for p in parts], [
            ('command', Span(0, 7)), ('sql', Span(7, 22)),
            ('command', Span(22, 39)), ('command', Span(39, 44))])
        self.assertEqual(''.join(text[p.span.start:p.span.end] for p in parts), text)

    def test_commands_inside_multiline_lexical_blocks_remain_sql(self):
        for block in ("'a;\n;exit\n''b\\'c'", '"a;\n;exit\n"',
                      '`a;\n;exit\n`', '[a;\n;exit\n]', '/* a;\n;exit\n*/'):
            with self.subTest(block=block):
                text = 'SELECT ' + block + ';\r\n;help\n'
                parts = classify(text)
                self.assertEqual([p.kind for p in parts], ['sql', 'command'])
                self.assertEqual(text[parts[0].span.start:parts[0].span.end], 'SELECT ' + block + ';\r\n')

    def test_only_full_unindented_command_lines_are_qualified(self):
        for line in (';h', ';help extra', ';exit;', ';autocommit', ';autocommit maybe',
                     ';autocommit on extra', ' ;help', '\t;exit', '; help', ';help\u00a0', ';read other.sql',
                     ';! touch marker', '! touch marker', ';shell touch marker', ';clear', ';;', '; ;'):
            with self.subTest(line=line):
                self.assertEqual([p.kind for p in classify(line)], ['unsupported'])

    def test_full_commands_allow_audited_trailing_ascii_blanks_without_changing_source(self):
        text = ';help \t\r\n;exit\t\n;autocommit\t on \t\n;autocommit  OFF\t'
        parts = classify(text)
        self.assertEqual([p.kind for p in parts], ['command'] * 4)
        self.assertEqual([text[p.span.start:p.span.end] for p in parts],
                         [';help \t\r\n', ';exit\t\n', ';autocommit\t on \t\n', ';autocommit  OFF\t'])

    def test_only_lf_starts_a_new_batch_line_and_empty_separators_remain_sql(self):
        for text in ('SELECT 1;\u2028;help', 'SELECT 1;\r;exit', ';\r\n;\n'):
            with self.subTest(text=text):
                self.assertEqual([p.kind for p in classify(text)], ['sql'])

    def test_procedural_regions_are_opaque_through_eof_including_inner_commands(self):
        for header in ('CREATE PROCEDURE p()', 'create /*x*/ or replace FUNCTION f()',
                       'DECLARE x INTEGER', 'BEGIN', 'CREATE PACKAGE p'):
            with self.subTest(header=header):
                text = 'SELECT 1;' + header + '\nBEGIN\nSELECT 2;\n;help\nEND;\nSELECT 3;'
                parts = classify(text)
                self.assertEqual([(p.kind, p.span.start) for p in parts], [('sql', 0), ('unsupported', 9)])
                self.assertEqual(parts[-1].span.end, len(text))

    def test_incomplete_procedural_lexical_tokens_remain_visible(self):
        for token in ("'open\\", '"open', '`open', '[open', '/* open'):
            with self.subTest(token=token):
                parts = classify('CREATE PROCEDURE p() AS BEGIN SELECT ' + token + '\n;exit')
                self.assertEqual(len(parts), 1)
                self.assertEqual(parts[0].kind, 'unsupported')
                self.assertTrue(parts[0].lexical_error)

    def test_commands_interleaved_with_pending_sql_are_opaque_without_fragment_syntax(self):
        for text in ('SELECT\n;help\n1;', 'SELECT (\r\n;exit\r\n1);',
                     'SELECT 1 +\n;autocommit on\n2;', 'SELECT\n;clear\n1;'):
            with self.subTest(text=text):
                parts = classify('SELECT 0;' + text + '\nSELECT 3;')
                self.assertEqual([(p.kind, p.span.start) for p in parts], [('sql', 0), ('unsupported', 9)])
                self.assertEqual(parts[-1].span.end, len(text) + 19)


if __name__ == '__main__':
    unittest.main()
