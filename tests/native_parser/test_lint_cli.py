"""Actual native qualification: missing worker artifacts are failures, never skips."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from cubrid_language.validation import PROFILE, Validator, WorkerConfig

ROOT = Path(__file__).resolve().parents[2]
BUILD = ROOT / 'native/parser-worker/build'


class NativeLintTests(unittest.TestCase):
    def test_actual_cli_retains_mixed_findings_when_native_diagnostics_truncate(self):
        text = 'SELECT ,;CREATE PROCEDURE p;' * 140
        result = self.run_cli('--format', 'json', '-', data=text.encode())
        self.assertEqual(result.returncode, 3)
        document = json.loads(result.stdout)['documents'][0]
        self.assertEqual((document['status'], document['coverage']), ('tool-error', 'partial'))
        self.assertEqual(len(document['diagnostics']), 256)
        self.assertEqual([d['code'] for d in document['diagnostics'][:2]], ['CUBRID-S1001', 'CUBRID-U1002'])
        self.assertEqual(document['diagnostics'][0]['span'], {'start': 0, 'end': 9})
        self.assertEqual(document['diagnostics'][1]['span'], {'start': 9, 'end': 28})
        self.assertEqual(document['diagnostics'][-1]['code'], 'CUBRID-T1002')
        self.assertEqual(document['diagnostics'][-1]['span']['end'], len(text))

    @classmethod
    def setUpClass(cls):
        manifest = json.loads((BUILD / 'manifest.json').read_bytes())
        cls.config = WorkerConfig(BUILD / 'parser-worker', Path(manifest['runtimePrefix']))
        if not cls.config.executable.is_file():
            raise FileNotFoundError(cls.config.executable)

    def test_public_validator_preserves_native_priority_and_original_unicode_crlf_spans(self):
        with Validator(self.config) as validator:
            result = validator.validate("SELECT '가😀';\r\nCREATE SERIAL s START WITH ;\r\nCREATE PROCEDURE p;", PROFILE, 'sql')
            self.assertEqual((result.status, result.coverage), ('syntax-error', 'partial'))
            self.assertEqual([(d.code, d.span.start, d.span.end) for d in result.diagnostics],
                             [('CUBRID-S1001', 12, 42), ('CUBRID-U1002', 42, 63)])

    def run_cli(self, *args, data=b'', cwd=None):
        console = Path(sys.executable).with_name('cubrid-lint')
        command = [str(console)] if console.is_file() else [sys.executable, '-m', 'cubrid_language.cli']
        environment = dict(os.environ)
        if not console.is_file() and 'PYTHONPATH' in environment:
            environment['PYTHONPATH'] = os.pathsep.join(str(Path(part).absolute())
                for part in environment['PYTHONPATH'].split(os.pathsep) if part)
        return subprocess.run([*command, '--parser-worker', str(self.config.executable),
                               '--runtime-prefix', str(self.config.runtime_prefix), *map(str, args)],
                              input=data, capture_output=True, cwd=cwd, env=environment, timeout=15)

    def test_public_validator_checks_empty_unknown_profiles_modes_and_native_results(self):
        with Validator(self.config) as validator:
            for text, status, coverage in (('', 'valid', 'complete'),
                                           ('SELECT 1', 'valid', 'complete'),
                                           ('CREATE SERIAL s START WITH ;', 'syntax-error', 'complete'),
                                           ('CREATE PROCEDURE p;', 'unsupported', 'none')):
                with self.subTest(text=text):
                    result = validator.validate(text, PROFILE, 'csql')
                    self.assertEqual((result.status, result.coverage), (status, coverage))
            unknown = validator.validate('', 'unknown-profile', 'sql')
            self.assertEqual((unknown.status, unknown.profile, unknown.diagnostics[0].code),
                             ('unsupported', 'unknown-profile', 'CUBRID-U1001'))
            self.assertEqual(validator.validate('', PROFILE, 'sql').status, 'valid')
        self.assertEqual(validator.validate('', PROFILE, 'sql').diagnostics[0].code, 'CUBRID-T1002')

    def test_actual_cli_exit_priority_and_ordered_json_documents(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, text in (('valid.sql', 'SELECT 1;'), ('empty.sql', ''),
                               ('unsupported.csql', 'CREATE PROCEDURE p;'),
                               ('syntax.sql', 'CREATE SERIAL s START WITH ;')):
                (root / name).write_bytes(text.encode('utf-8'))
            for paths, code, status in ((['valid.sql', 'empty.sql'], 0, 'valid'),
                                         (['valid.sql', 'unsupported.csql'], 2, 'unsupported'),
                                         (['unsupported.csql', 'syntax.sql', 'valid.sql'], 1, 'syntax-error'),
                                         (['unsupported.csql', 'syntax.sql', 'missing.sql', 'valid.sql'], 3, 'tool-error')):
                with self.subTest(paths=paths):
                    result = self.run_cli('--format', 'json', *paths, cwd=root)
                    self.assertEqual(result.returncode, code, result.stderr)
                    value = json.loads(result.stdout)
                    self.assertEqual(value['status'], status)
                    self.assertEqual([d['path'] for d in value['documents']], paths)
                    self.assertEqual(result.stderr, b'')

    def test_actual_cli_preserves_original_bytes_and_human_codepoint_columns(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'span.sql').write_bytes("SELECT '가😀';\r\nCREATE SERIAL s START WITH ;".encode('utf-8'))
            result = self.run_cli('--format', 'json', 'span.sql', cwd=root)
            document = json.loads(result.stdout)['documents'][0]
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertEqual(document['diagnostics'][0]['span'], {'start': 12, 'end': 42})
            self.assertEqual(document['diagnostics'][0]['rangePrecision'], 'statement')
            (root / 'column.sql').write_bytes("SELECT '가😀';CREATE SERIAL s START WITH ;".encode('utf-8'))
            result = self.run_cli('column.sql', cwd=root)
            self.assertEqual(result.returncode, 1)
            self.assertIn(b'column.sql:1:13: error CUBRID-S1001', result.stdout)
            self.assertIn(b'column.sql: syntax-error (complete,', result.stdout)
            self.assertEqual(result.stderr, b'')

    def test_actual_cli_stdin_eof_and_unknown_profile_have_distinct_exits(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_cli('--format', 'json', '-', data="SELECT '가😀'".encode('utf-8'), cwd=directory)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)['documents'][0]['status'], 'valid')
            result = self.run_cli('--profile', 'unknown-profile', '--format', 'json', '-', cwd=directory)
            self.assertEqual(result.returncode, 2, result.stderr)
            document = json.loads(result.stdout)['documents'][0]
            self.assertEqual((document['profile'], document['diagnostics'][0]['code']),
                             ('unknown-profile', 'CUBRID-U1001'))

    def test_actual_cli_csql_shell_and_include_constructs_stay_unsupported_without_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'script.csql').write_bytes(b';! touch marker\n;read other.sql\n')
            result = self.run_cli('--format', 'json', 'script.csql', cwd=root)
            self.assertEqual(result.returncode, 2, result.stderr)
            document = json.loads(result.stdout)['documents'][0]
            self.assertEqual((document['scriptMode'], document['status']), ('csql', 'unsupported'))
            self.assertTrue(all(d['code'] == 'CUBRID-U1002' for d in document['diagnostics']))
            self.assertFalse((root / 'marker').exists())

    def test_actual_cli_config_profile_is_not_silently_substituted(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / '.cubrid-language.json').write_text('{"profile":"unqualified"}')
            (root / 'valid.sql').write_bytes(b'SELECT 1;')
            result = self.run_cli('--format', 'json', 'valid.sql', cwd=root)
            self.assertEqual(result.returncode, 2, result.stderr)
            result = self.run_cli('--profile', PROFILE, '--format', 'json', 'valid.sql', cwd=root)
            self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
