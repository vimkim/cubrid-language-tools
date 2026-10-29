import unittest

from cubrid_language import complete
from cubrid_language.validation import PROFILE, Validator


class ShowHintAuthoringTests(unittest.TestCase):
    def test_hint_completion_replaces_whole_word(self):
        text = 'SELECT /*+ USE_NLwrong */ 1;'
        result = complete(text, text.index('wrong'), PROFILE)
        self.assertTrue(result.allowed)
        self.assertEqual(text[result.replacement.start:result.replacement.end], 'USE_NLwrong')
        self.assertIn('USE_NL', [item.text for item in result.items])

    def test_unknown_hint_survives_missing_native_runtime(self):
        text = 'SELECT /*+ NOT_A_HINT */ 1;'
        with Validator() as validator:
            result = validator.validate(text, PROFILE, 'sql')
        self.assertEqual(result.status, 'tool-error')
        self.assertIn('CUBRID-T1001', [d.code for d in result.diagnostics])
        warning = next(d for d in result.diagnostics if d.code == 'CUBRID-A1001')
        self.assertEqual((warning.severity, warning.category), ('warning', 'authoring'))
        self.assertEqual(text[warning.span.start:warning.span.end], 'NOT_A_HINT')

class AuthoringCoverageTests(unittest.TestCase):
    def test_complete_hints_in_all_comment_forms_and_multiple_names(self):
        for opener, closer in (('/*+', ' */'), ('--+', '\n'), ('//+', '\n')):
            for prefix in ('use_n', 'ORDERED use_n'):
                text = 'SELECT ' + opener + ' ' + prefix + 'bad' + closer + ' 1;'
                cursor = text.index('bad')
                result = complete(text, cursor, PROFILE)
                self.assertIn('USE_NL', [item.text for item in result.items])
                self.assertEqual(text[result.replacement.start:result.replacement.end], 'use_nbad')

    def test_alias_completion_without_a_schema(self):
        text = 'SELECT /*+ USE_NL(a|bad) */ * FROM account a;'
        cursor = text.index('|')
        result = complete(text.replace('|', ''), cursor, PROFILE)
        self.assertIn('a', [item.text for item in result.items])
        self.assertEqual(result.replacement.end - result.replacement.start, 4)

    def test_suppression_and_incomplete_input(self):
        from cubrid_language import authoring_diagnostics
        for text in ("SELECT '/*+ BOGUS */';", 'SELECT /* BOGUS */ 1;',
                     'SELECT /*+ BOGUS', 'SELECT /*+ USE_NL(BOGUS',
                     'CREATE PROCEDURE p AS BEGIN SELECT /*+ BOGUS */ 1; END;',
                     'CREATE TRIGGER t BEFORE INSERT ON a EXECUTE SELECT /*+ BOGUS */ 1;',
                     'SELECT /*+ USE_NL("a(b)") */ 1;',
                     ';read SELECT /*+ BOGUS */ 1;\n'):
            with self.subTest(text=text):
                self.assertEqual(authoring_diagnostics(text, PROFILE, 'csql'), ())
        self.assertEqual(authoring_diagnostics('SELECT /*+ BOGUS */ 1;', 'unknown'), ())
        self.assertFalse(complete('CREATE PROCEDURE p AS BEGIN SELECT /*+ USE_N', 44, PROFILE).allowed)

    def test_rules_and_correct_counterexamples_with_original_ranges(self):
        from cubrid_language import authoring_diagnostics
        cases = (
            ('SELECT /*+ BOGUS */ 1;', 'CUBRID-A1001', 'BOGUS'),
            ('SELECT /*+ USE_NL((a)) */ 1;', 'CUBRID-A1002', '((a))'),
            ('SELECT /*+ USE_NL(a */ 1;', 'CUBRID-A1002', '(a'),
            ('SHOW BOGUS;', 'CUBRID-A1003', 'BOGUS'),
            ('SHOW CREATE BOGUS;', 'CUBRID-A1003', 'BOGUS'),
            ('SELECT DISTINCT /*+ ORDERED */ 1;', 'CUBRID-A1004', '/*+ ORDERED */'),
        )
        for source, code, span in cases:
            text = '-- 가😀\r\n' + source
            with self.subTest(code=code):
                finding = next(d for d in authoring_diagnostics(text, PROFILE) if d.code == code)
                self.assertEqual(text[finding.span.start:finding.span.end], span)
        line = 'SELECT --+ USE_NL(a\r\n1;'
        warning = authoring_diagnostics(line, PROFILE)[0]
        self.assertEqual(line[warning.span.start:warning.span.end], '(a')
        malformed = authoring_diagnostics('SELECT /*+ BOGUS(a */ 1;', PROFILE)
        self.assertEqual([d.code for d in malformed], ['CUBRID-A1001', 'CUBRID-A1002'])
        for text in ('SELECT /*+ ORDERED USE_NL(a) */ 1;', 'SELECT /*+ SQL_CACHE SQL_NO_CACHE */ 1;',
                     'SHOW FULL TIMEZONES;', 'SHOW INDEX HEADER OF t.i;', 'SHOW TABLES;',
                     'SELECT /*+ ORDERED */ DISTINCT 1;', 'SHOW', 'SHOW TAB'):
            with self.subTest(text=text):
                self.assertEqual(authoring_diagnostics(text, PROFILE), ())

    def test_limit_one_keeps_native_failure_context(self):
        from pathlib import Path
        from cubrid_language.validation import WorkerConfig
        config = WorkerConfig(Path('/nonexistent/worker'), Path('/nonexistent/runtime'), max_diagnostics=1)
        with Validator(config) as validator:
            result = validator.validate('SELECT /*+ BOGUS */ 1;', PROFILE, 'sql')
        self.assertEqual(result.status, 'tool-error')
        self.assertEqual(len(result.diagnostics), 1)
        self.assertIn('limit exceeded', result.diagnostics[0].message)
        self.assertIn('CUBRID-T1001', result.diagnostics[0].message)

class InventoryTests(unittest.TestCase):
    def test_portable_grammar_fixture_and_mutated_input(self):
        from pathlib import Path
        import subprocess
        import sys
        import tempfile
        root = Path(__file__).resolve().parents[1]
        fixture = root / 'tests/fixtures/show_hint_grammar.y'
        tool = root / 'tools/check_show_hint_inventory.py'
        good = subprocess.run([sys.executable, str(tool), str(fixture)], capture_output=True, text=True)
        self.assertEqual(good.returncode, 0, good.stderr)
        with tempfile.TemporaryDirectory() as directory:
            changed = Path(directory) / 'grammar.y'
            changed.write_text(fixture.read_text().replace('INIT_PT_HINT("USE_NL",', 'INIT_PT_HINT("BROKEN",'))
            bad = subprocess.run([sys.executable, str(tool), str(changed)], capture_output=True, text=True)
        self.assertNotEqual(bad.returncode, 0)
        self.assertIn('inventory differs', bad.stderr)

    def test_cli_reports_warning_with_missing_runtime(self):
        import json
        import subprocess
        import sys
        text = 'SELECT /*+ BOGUS */ 1;'
        process = subprocess.run([sys.executable, '-m', 'cubrid_language.cli', '--format', 'json', '-'],
                                 input=text, text=True, capture_output=True)
        self.assertEqual(process.returncode, 3, process.stderr)
        findings = json.loads(process.stdout)['documents'][0]['diagnostics']
        warning = next(d for d in findings if d['code'] == 'CUBRID-A1001')
        self.assertEqual(text[warning['span']['start']:warning['span']['end']], 'BOGUS')
        self.assertEqual(warning['category'], 'authoring')
