from contextlib import redirect_stdout
from io import StringIO
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


class LintCliTests(unittest.TestCase):
    def run_cli(self, *args, data=b'', cwd=None):
        return subprocess.run([sys.executable, '-m', 'cubrid_language.cli', *map(str, args)],
                              input=data, capture_output=True, cwd=cwd, timeout=15)

    def test_missing_worker_is_a_json_document_result_through_the_command_entry_point(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_cli('--format', 'json', '-', cwd=directory)
        self.assertEqual(result.returncode, 3, result.stderr)
        value = json.loads(result.stdout)
        self.assertEqual((value['schemaVersion'], value['offsetEncoding'], value['status']),
                         (1, 'unicode-codepoints', 'tool-error'))
        self.assertEqual(len(value['documents']), 1)
        self.assertEqual(value['documents'][0]['path'], '-')
        self.assertEqual(value['documents'][0]['diagnostics'][0]['code'], 'CUBRID-T1001')
        self.assertEqual(result.stderr, b'')

    def test_input_failures_remain_ordered_documents_and_do_not_prevent_other_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'bad.sql').write_bytes(b'\xff')
            (root / 'nul.sql').write_bytes(b'SELECT 1;\0')
            (root / 'empty.sql').write_bytes(b'')
            result = self.run_cli('--format', 'json', 'missing.sql', 'bad.sql', 'nul.sql',
                                  'empty.sql', '.', '-', data=b'\xff', cwd=root)
            self.assertEqual(result.returncode, 3, result.stderr)
            value = json.loads(result.stdout)
            self.assertEqual([item['path'] for item in value['documents']],
                             ['missing.sql', 'bad.sql', 'nul.sql', 'empty.sql', '.', '-'])
            self.assertEqual([item['diagnostics'][0]['code'] for item in value['documents']],
                             ['CUBRID-T1003', 'CUBRID-T1003', 'CUBRID-T1003',
                              'CUBRID-T1001', 'CUBRID-T1003', 'CUBRID-T1003'])
            self.assertEqual(result.stderr, b'')

    def test_malformed_arguments_use_exit_three_and_never_print_a_traceback(self):
        for args in ((), ('--format', 'yaml', '-'), ('--script-mode', 'auto', '-'),
                     ('--ignore-unsupported', '-'), ('--profile',), ('--prof', 'wrong', '-')):
            with self.subTest(args=args):
                result = self.run_cli(*args)
                self.assertEqual(result.returncode, 3, result.stderr)
                self.assertEqual(result.stdout, b'')
                self.assertIn(b'cubrid-lint: error:', result.stderr)
                self.assertNotIn(b'Traceback', result.stderr)
        help_result = self.run_cli('--help')
        self.assertEqual(help_result.returncode, 0)
        self.assertIn(b'--parser-worker', help_result.stdout)

    def test_stdin_is_read_once_as_bytes_and_duplicate_stdin_is_rejected_before_read(self):
        from cubrid_language.cli import main

        class BinaryInput:
            def __init__(self):
                self.buffer = self
                self.reads = 0

            def read(self, size):
                self.reads += 1
                if self.reads > 1:
                    raise AssertionError('stdin was read more than once')
                return b'-- \xea\xb0\x80\xf0\x9f\x98\x80\r\nSELECT 1;'

        source = BinaryInput()
        with patch('sys.stdin', source), redirect_stdout(StringIO()) as output:
            self.assertEqual(main(['--format', 'json', '-']), 3)
        self.assertEqual(source.reads, 1)
        self.assertEqual(json.loads(output.getvalue())['documents'][0]['diagnostics'][0]['span'],
                         {'start': 0, 'end': 16})
        source = BinaryInput()
        with patch('sys.stdin', source), redirect_stdout(StringIO()) as output:
            self.assertEqual(main(['--format', 'json', '-', '-']), 3)
        self.assertEqual(source.reads, 0)
        documents = json.loads(output.getvalue())['documents']
        self.assertEqual([item['diagnostics'][0]['code'] for item in documents],
                         ['CUBRID-T1003', 'CUBRID-T1003'])

    def test_project_metadata_and_explicit_flags_select_profile_and_script_mode_per_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / '.cubrid-language.json').write_text('{"profile":"project","scriptMode":"csql"}')
            (root / 'job.sql').write_bytes(b'')
            result = self.run_cli('job.sql', '--format', 'json', cwd=root)
            document = json.loads(result.stdout)['documents'][0]
            self.assertEqual((document['profile'], document['scriptMode']), ('project', 'csql'))
            result = self.run_cli('--profile', 'flag', 'job.sql', '--format', 'json',
                                  '--script-mode', 'sql', cwd=root)
            document = json.loads(result.stdout)['documents'][0]
            self.assertEqual((document['profile'], document['scriptMode']), ('flag', 'sql'))
            (root / '.cubrid-language.json').unlink()
            (root / 'job.csql').write_bytes(b'')
            result = self.run_cli('--format', 'json', 'job.csql', 'job.sql', '-', cwd=root)
            self.assertEqual([d['scriptMode'] for d in json.loads(result.stdout)['documents']],
                             ['csql', 'sql', 'sql'])

    def test_project_metadata_cannot_select_commands_credentials_or_a_runtime(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for config in ({'parserWorker': 'touch marker'}, {'runtimePrefix': '/untrusted'},
                           {'command': 'touch marker'}, {'password': 'secret'}):
                with self.subTest(config=config):
                    (root / '.cubrid-language.json').write_text(json.dumps(config))
                    result = self.run_cli('--format', 'json', '-', cwd=root)
                    self.assertEqual(result.returncode, 3)
                    self.assertEqual(json.loads(result.stdout)['documents'][0]['diagnostics'][0]['code'],
                                     'CUBRID-T1003')
                    self.assertFalse((root / 'marker').exists())
                    self.assertNotIn(b'secret', result.stdout)

    def test_console_script_is_registered_by_the_distribution(self):
        from importlib.metadata import distribution
        scripts = {entry.name: entry.value for entry in distribution('cubrid-language-tools').entry_points
                   if entry.group == 'console_scripts'}
        self.assertEqual(scripts.get('cubrid-lint'), 'cubrid_language.cli:main')

    def test_explicit_worker_configuration_requires_both_paths_and_never_uses_ambient_values(self):
        with tempfile.TemporaryDirectory() as directory:
            for args, code in ((('--parser-worker', '/nonexistent/worker'), 'CUBRID-T1003'),
                               (('--runtime-prefix', '/nonexistent/runtime'), 'CUBRID-T1003'),
                               (('--parser-worker', '/nonexistent/worker', '--runtime-prefix', '/nonexistent/runtime'),
                                'CUBRID-T1001')):
                with self.subTest(args=args):
                    result = self.run_cli('--format', 'json', *args, '-', cwd=directory)
                    self.assertEqual(result.returncode, 3)
                    self.assertEqual(json.loads(result.stdout)['documents'][0]['diagnostics'][0]['code'], code)
            environment = dict(os.environ, CUBRID='/untrusted/runtime',
                               CUBRID_PARSER_WORKER='/untrusted/worker')
            result = subprocess.run([sys.executable, '-m', 'cubrid_language.cli', '--format', 'json', '-'],
                                    input=b'', capture_output=True, env=environment, cwd=directory, timeout=15)
            self.assertEqual(json.loads(result.stdout)['documents'][0]['diagnostics'][0]['code'], 'CUBRID-T1001')

    def test_oversize_input_is_rejected_without_truncation_or_native_prerequisites(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_cli('--format', 'json', '-', data=b' ' * (8 * 1024 * 1024 + 1), cwd=directory)
        self.assertEqual(result.returncode, 3, result.stderr)
        document = json.loads(result.stdout)['documents'][0]
        self.assertEqual(document['diagnostics'][0]['code'], 'CUBRID-T1003')
        self.assertIn('byte limit', document['diagnostics'][0]['message'])


if __name__ == '__main__':
    unittest.main()
