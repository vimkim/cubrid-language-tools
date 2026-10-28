"""Mandatory actual-native CSQL library and command qualification."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from cubrid_language.validation import PROFILE, Validator, WorkerConfig

ROOT = Path(__file__).resolve().parents[2]
BUILD = ROOT / 'native/parser-worker/build'


class NativeScriptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        manifest = json.loads((BUILD / 'manifest.json').read_bytes())
        cls.config = WorkerConfig(BUILD / 'parser-worker', Path(manifest['runtimePrefix']))
        if not cls.config.executable.is_file():
            raise FileNotFoundError(cls.config.executable)

    def run_cli(self, *args, data=b'', cwd=None, trace=None):
        console = Path(sys.executable).with_name('cubrid-lint')
        command = [str(console)] if console.is_file() else [sys.executable, '-m', 'cubrid_language.cli']
        environment = dict(os.environ)
        if 'PYTHONPATH' in environment:
            environment['PYTHONPATH'] = os.pathsep.join(str(Path(p).absolute())
                for p in environment['PYTHONPATH'].split(os.pathsep) if p)
        if trace is not None:
            tracer = shutil.which('strace')
            if tracer is None:
                raise FileNotFoundError('mandatory no-execution qualification requires strace')
            command = [tracer, '-f', '-e', 'trace=%file,%process', '-o', str(trace), *command]
        return subprocess.run([*command, '--parser-worker', str(self.config.executable),
                               '--runtime-prefix', str(self.config.runtime_prefix), *map(str, args)],
                              input=data, capture_output=True, cwd=cwd, env=environment, timeout=15)

    def test_commands_and_sql_share_complete_coverage_without_exiting(self):
        text = ";HeLp \t\r\nSELECT '가😀;';\r\n;exit\t\r\n;AUTOCOMMIT\t on \t\nSELECT 2"
        with Validator(self.config) as validator:
            result = validator.validate(text, PROFILE, 'csql')
            self.assertEqual((result.status, result.coverage, result.statement_kinds),
                             ('valid', 'complete', ('PT_SELECT', 'PT_SELECT')))
            self.assertEqual(validator.validate(';help', PROFILE, 'sql').status, 'unsupported')

    def test_translated_native_syntax_and_unsupported_spans_keep_original_unicode_crlf(self):
        text = ";help\r\nSELECT '가😀';\r\n;read other.sql\r\nCREATE SERIAL s START WITH ;\r\n;exit"
        with Validator(self.config) as validator:
            result = validator.validate(text, PROFILE, 'csql')
        self.assertEqual((result.status, result.coverage), ('syntax-error', 'partial'))
        self.assertEqual([(d.code, d.span.start, d.span.end, d.range_precision) for d in result.diagnostics],
                         [('CUBRID-U1002', 21, 38, 'statement'), ('CUBRID-S1001', 38, 66, 'statement')])

    def test_native_lexical_blocks_escapes_and_final_eof_keep_command_boundaries(self):
        cases = [(";help\nSELECT 'a;''b\\\'c';\r\n;exit\nSELECT 2", 'valid'),
                 (";help\nSELECT 'a\n;exit\n';\r\n;exit", 'valid'),
                 (';help\n/* ;\r\n;exit\r\n*/ SELECT 1;\n;exit', 'valid'),
                 (';help\n-- ;exit\n// ;help\nSELECT 1', 'valid'),
                 (';help\nSELECT "a\n;exit\nb" FROM absent;', 'unsupported'),
                 (';help\nSELECT `a\n;exit\nb` FROM absent;', 'unsupported'),
                 (';help\nSELECT [a\n;exit\nb] FROM absent;', 'unsupported')]
        with Validator(self.config) as validator:
            for text, status in cases:
                with self.subTest(text=text):
                    result = validator.validate(text, PROFILE, 'csql')
                    self.assertEqual(result.status, status, result)
                    self.assertFalse(any(d.message.startswith('CSQL construct') for d in result.diagnostics))
            for token in ("'open\\", '"open', '`open', '[open', '/* open'):
                text = ';help\r\nSELECT ' + token + '\r\n;exit'
                with self.subTest(token=token):
                    result = validator.validate(text, PROFILE, 'csql')
                    self.assertEqual(result.status, 'syntax-error', result)
                    self.assertEqual((result.diagnostics[0].span.start, result.diagnostics[0].span.end), (7, len(text)))

    def test_procedures_and_pending_sql_are_unsupported_without_inner_successes(self):
        with Validator(self.config) as validator:
            for text in ('CREATE PROCEDURE p() AS BEGIN SELECT 1; SELECT 2; END;\nSELECT 3;',
                         'SELECT\n;help\n1;', 'SELECT (\r\n;exit\r\n1);',
                         'SELECT 1 +\n;autocommit on\n2;', 'SELECT\n;clear\n1;'):
                with self.subTest(text=text):
                    result = validator.validate(text, PROFILE, 'csql')
                    self.assertEqual((result.status, result.coverage, result.statement_kinds), ('unsupported', 'none', ()))
                    self.assertEqual([d.code for d in result.diagnostics], ['CUBRID-U1002'])
            result = validator.validate("CREATE PROCEDURE p() AS BEGIN SELECT 'open", PROFILE, 'csql')
            self.assertEqual((result.status, result.coverage), ('syntax-error', 'none'))
            self.assertEqual([d.code for d in result.diagnostics], ['CUBRID-S1001', 'CUBRID-U1002'])

    def test_real_cli_json_and_human_results_match_library_script_spans(self):
        text = ";help\r\nSELECT '가😀';\r\n;read other.sql\r\nCREATE SERIAL s START WITH ;\r\n;exit"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'script.csql').write_bytes(text.encode('utf-8'))
            result = self.run_cli('--format', 'json', 'script.csql', cwd=root)
            with Validator(self.config) as validator:
                library = validator.validate(text, PROFILE, 'csql')
            value = json.loads(result.stdout)
            document = value['documents'][0]
            self.assertEqual((result.returncode, value['status'], document['coverage']), (1, 'syntax-error', 'partial'))
            self.assertEqual(document['diagnostics'], [d.to_dict() for d in library.diagnostics])
            self.assertEqual(result.stderr, b'')
            human = self.run_cli('script.csql', cwd=root)
            self.assertIn(b'script.csql:4:1: error CUBRID-S1001', human.stdout)
            self.assertIn(b'script.csql:3:1: warning CUBRID-U1002', human.stdout)
            accepted = self.run_cli('--script-mode', 'csql', '--format', 'json', '-',
                                    data=b';help \t\n;exit\t\n;autocommit\t on \t\n;autocommit  off\t\nSELECT 1', cwd=root)
            self.assertEqual(accepted.returncode, 0, accepted.stdout)
            unknown = self.run_cli('--profile', 'unknown-profile', '--script-mode', 'csql', '--format', 'json',
                                   '-', data=b';help\n;exit', cwd=root)
            self.assertEqual(unknown.returncode, 2, unknown.stdout)
            self.assertEqual(json.loads(unknown.stdout)['documents'][0]['coverage'], 'none')
            for pending in (b'SELECT\n;help\n1;', b'SELECT (\r\n;exit\r\n1);'):
                unsupported = self.run_cli('--script-mode', 'csql', '--format', 'json', '-', data=pending, cwd=root)
                self.assertEqual(unsupported.returncode, 2, unsupported.stdout)
                self.assertEqual([d['code'] for d in json.loads(unsupported.stdout)['documents'][0]['diagnostics']], ['CUBRID-U1002'])

    def test_real_cli_includes_and_shell_text_are_never_opened_or_executed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reference = root / 'never-read-08.sql'
            reference.write_text('CREATE SERIAL s START WITH ;')
            marker = root / 'never-created-08'
            text = f';read {reference}\n;! touch {marker}\n! touch {marker}\n;help\nSELECT 1'
            (root / 'safety.csql').write_text(text)
            trace = root / 'syscalls.log'
            result = self.run_cli('--format', 'json', 'safety.csql', cwd=root, trace=trace)
            self.assertEqual(result.returncode, 2, result.stderr)
            diagnostics = json.loads(result.stdout)['documents'][0]['diagnostics']
            self.assertEqual([d['code'] for d in diagnostics], ['CUBRID-U1002'] * 3)
            syscalls = trace.read_text()
            self.assertNotIn(str(reference), syscalls)
            self.assertNotIn('/bin/sh', syscalls)
            self.assertNotIn('/usr/bin/touch', syscalls)
            self.assertFalse(marker.exists())
