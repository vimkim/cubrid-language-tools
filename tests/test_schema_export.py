"""Schema export through the installed CLI and importable acquisition adapter."""

import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from cubrid_language import complete
from cubrid_language.schema import load_snapshot


HEADER = 'kind\tlogin_name\towner_name\tclass_name\titem_name\titem_type\n'
IDENTITY = 'identity\tDBA\tDBA\tdemodb\tdemodb\tDATABASE\n'
CATALOG = HEADER + IDENTITY + (
    'relation\tDBA\tDBA\t고객\t고객\tCLASS\n'
    'column\tDBA\tDBA\t고객\t이름\\t표\\n줄\\\\끝\tINSTANCE\n'
    'index\tDBA\tDBA\t고객\t고객 인덱스\tINDEX\n'
    'relation\tDBA\tOTHER\t고객\t고객\tVCLASS\n'
    'system\tDBA\tDBA\tdb_class\tdb_class\tVCLASS\n'
    'user\tDBA\tDBA\tDBA\tDBA\tUSER\n'
    'user\tDBA\tDBA\t사용자\t사용자\tUSER\n'
)
STUB = '''#!/usr/bin/env python3
import json, os, pathlib, signal, sys, time
root = pathlib.Path(os.environ['SCHEMA_TEST_ROOT'])
(root / 'launch.json').write_text(json.dumps({'argv': sys.argv[1:], 'cwd': os.getcwd(), 'pid': os.getpid()}))
mode = (root / 'mode').read_text()
if mode in ('fork', 'fork_exit'):
    child = os.fork()
    if child == 0:
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        (root / 'descendant').write_text(str(os.getpid()))
        while True: time.sleep(1)
    while not (root / 'descendant').exists(): time.sleep(.005)
    if mode == 'fork_exit':
        sys.stdout.buffer.write((root / 'catalog').read_bytes())
        sys.stdout.flush()
        os._exit(0)
if mode in ('hang', 'fork'):
    while True: time.sleep(1)
if mode in ('stdout_flood', 'stderr_flood', 'both_flood'):
    if mode == 'both_flood':
        os.write(1, b'x' * (9 * 1024 * 1024))
        os.write(2, b'y' * (9 * 1024 * 1024))
    else:
        fd = 1 if mode == 'stdout_flood' else 2
        while True: os.write(fd, b'x' * 65536)
    sys.exit(0)
if mode == 'stderr': os.write(2, b'ERROR: secret-password private-command')
if mode == 'exit': sys.exit(7)
if mode == 'cuberr': pathlib.Path('cub.err').write_text('private-command')
sys.stdout.buffer.write((root / 'catalog').read_bytes())
'''


@unittest.skipUnless(os.name == 'posix', 'export requires owned POSIX process groups')
class SchemaExportTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.csql = self.root / 'controlled-csql'
        self.csql.write_text(STUB)
        self.csql.chmod(0o700)
        (self.root / 'catalog').write_text(CATALOG, encoding='utf-8')
        (self.root / 'mode').write_text('normal')
        self.environment = dict(os.environ, SCHEMA_TEST_ROOT=str(self.root))
        self.console = [sys.executable, '-m', 'cubrid_language.schema_cli', 'export', '--csql', str(self.csql)]

    def run_cli(self, command='csql -udba demodb@localhost -C', password=None, *, data=None, extra=()):
        if data is None:
            data = json.dumps({'requestVersion': 1, 'command': command, 'password': password}).encode()
        return subprocess.run([*self.console, *extra, '--request-stdin'], input=data,
                              capture_output=True, env=self.environment, cwd=self.root, timeout=5)

    def assert_failure(self, result, code):
        self.assertEqual(code, result.returncode, result.stderr)
        self.assertEqual(b'', result.stdout)
        self.assertLess(len(result.stderr), 200)
        for secret in (b'secret-password', b'private-command', str(self.root).encode(), b'Traceback'):
            self.assertNotIn(secret, result.stderr)

    def launched(self):
        return json.loads((self.root / 'launch.json').read_text())

    def test_original_direct_arguments_export_complete_metadata(self):
        result = subprocess.run([*self.console, '--', '-udba', 'demodb', '-C'], capture_output=True,
                                env=self.environment, cwd=self.root, timeout=5)
        self.assertEqual(0, result.returncode, result.stderr)
        snapshot = json.loads(result.stdout)
        self.assertEqual('', result.stderr.decode())
        self.assertEqual({'endpoint': 'demodb'}, snapshot['source'])
        self.assertEqual(('DBA', 'demodb', ['DBA', '사용자']),
                         (snapshot['user'], snapshot['database'], snapshot['users']))
        path = self.root / 'snapshot.json'
        path.write_bytes(result.stdout)
        schema = load_snapshot(path).schema
        self.assertIsNotNone(schema)
        own = next(r for r in schema.relations if r.owner == 'DBA' and r.name == '고객')
        self.assertEqual(('이름\t표\n줄\\끝',), own.columns)
        self.assertEqual(('고객 인덱스',), own.indexes)
        self.assertTrue(next(r for r in schema.relations if r.name == 'db_class').system)
        text = 'SELECT * FROM 고'
        self.assertIn('고객', [item.text for item in complete(text, len(text), 'cubrid-11.5.0.2704-cc94778', schema).items])
        argv = self.launched()['argv']
        self.assertIn('-C', argv)
        self.assertEqual('', argv[argv.index('-p') + 1])
        self.assertIn('CURRENT_USER', argv[argv.index('-c') + 1])
        self.assertIn('DATABASE()', argv[argv.index('-c') + 1])

    def test_password_precedence_quoting_and_descriptive_program(self):
        for command, password, expected in (
            ('/private-command/csql --user "dba" --password="inline pass" demodb@localhost', None, 'inline pass'),
            ('csql -u dba -pinline demodb', 'secret-password', 'secret-password'),
            ('csql --user=dba --password inline demodb --CS-mode', '', ''),
            ('-udba -p "dollar$(private-command)" demodb', None, 'dollar$(private-command)'),
        ):
            with self.subTest(command=command):
                result = self.run_cli(command, password)
                self.assertEqual(0, result.returncode, result.stderr)
                argv = self.launched()['argv']
                self.assertEqual(expected, argv[argv.index('-p') + 1])
                self.assertEqual('dba', argv[argv.index('-u') + 1])
                self.assertIn('-C', argv)
                if expected:
                    self.assertNotIn(expected.encode(), result.stderr)
                    self.assertNotIn(expected.encode(), result.stdout)

    def test_unsafe_or_ambiguous_commands_reject_before_launch(self):
        for command in (
            '', 'csql', 'csql -S demodb', 'csql --SA-mode demodb',
            'csql --sysadm demodb', 'csql --sysadm-rebuild-catalog demodb',
            'csql -c "drop table private-command" demodb', 'csql -i private-command demodb',
            'csql -o private-command demodb', 'csql --unknown demodb',
            'csql -u first -u second demodb', 'csql -p first -p second demodb',
            'csql demodb another', 'csql demodb;private-command', 'csql demodb | private-command',
            'csql -u', 'csql -u -C demodb', 'csql "unterminated', 'csql demo\x00db',
        ):
            with self.subTest(command=command):
                self.assert_failure(self.run_cli(command), 2)
                self.assertFalse((self.root / 'launch.json').exists())

    def test_strict_request_envelope_and_redacted_cli_errors(self):
        for data in (
            b'\xff', b'[]', b'{}', b'{"requestVersion":true,"command":"csql demodb"}',
            b'{"requestVersion":1,"command":"csql demodb","extra":"private-command"}',
            b'{"requestVersion":1,"command":"csql demodb","command":"secret-password"}',
            b'{"requestVersion":1,"command":"csql demodb","password":1}',
            b'{"requestVersion":1,"command":"csql demodb","password":"\\ud800"}',
            b'{"requestVersion":1,"command":42}', b'[' * 2000,
            b'{"requestVersion":1,"command":"csql demodb"} trailing', b'x' * 65537,
        ):
            with self.subTest(data=data[:80]):
                self.assert_failure(self.run_cli(data=data), 2)
                self.assertFalse((self.root / 'launch.json').exists())
        for extra in (('--timeout', 'private-command'), ('--timeout', 'nan'), ('--timeout', '0'),
                      ('--timeout', '301'), ('--private-command',), ('--', 'demodb')):
            self.assert_failure(self.run_cli(extra=extra), 2)
        self.assertFalse((self.root / 'launch.json').exists())

    def test_identity_allows_empty_and_restricted_catalog(self):
        for output in (HEADER + IDENTITY, HEADER + IDENTITY + 'relation\tDBA\tDBA\tvisible\tvisible\tCLASS\n'):
            (self.root / 'catalog').write_text(output)
            result = self.run_cli()
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual('DBA', json.loads(result.stdout)['user'])

    def test_invalid_catalog_is_never_a_successful_empty_or_partial_snapshot(self):
        for output in (
            b'', HEADER.encode(), (HEADER + IDENTITY * 2).encode(),
            (HEADER + IDENTITY.replace('demodb', 'another')).encode(),
            (HEADER + IDENTITY + 'relation\tOTHER\tOTHER\tt\tt\tCLASS\n').encode(),
            (HEADER + IDENTITY + 'column\tDBA\tDBA\torphan\tc\tINSTANCE\n').encode(),
            (HEADER + IDENTITY + 'relation\tDBA\tDBA\tt\tt\tVIEW\n').encode(),
            (HEADER + IDENTITY + 'relation\tDBA\tDBA\tt\tt\tCLASS\n' * 2).encode(),
            (HEADER + IDENTITY + 'short\trow\n').encode(),
            (CATALOG + 'ERROR: private-command\n').encode(),
            CATALOG.replace('고객 인덱스', 'bad\\x').encode(), CATALOG.encode() + b'\xff',
        ):
            with self.subTest(output=output[:100]):
                (self.root / 'catalog').write_bytes(output)
                self.assert_failure(self.run_cli(), 3)

    def test_real_csql_catalog_framing(self):
        fixture = json.loads((Path(__file__).parent / 'fixtures/schema-csql-11.5.json').read_text())
        (self.root / 'catalog').write_text(fixture['stdout'], encoding='utf-8')
        result = self.run_cli('csql -udba testdb -C')
        self.assertEqual(0, result.returncode, result.stderr)
        snapshot = json.loads(result.stdout)
        people = next(r for r in snapshot['relations'] if r['name'] == 'schema_people')
        self.assertEqual(['id', 'person_name'], people['columns'])
        self.assertEqual(['idx_schema_person'], people['indexes'])
        self.assertEqual('testdb', snapshot['database'])

    def test_child_errors_are_redacted_even_with_exit_zero(self):
        for mode in ('stderr', 'exit'):
            (self.root / 'mode').write_text(mode)
            self.assert_failure(self.run_cli(password='secret-password'), 3)

    def test_logs_are_confined_to_a_private_removed_working_directory(self):
        (self.root / 'mode').write_text('cuberr')
        result = self.run_cli()
        self.assertEqual(0, result.returncode, result.stderr)
        cwd = Path(self.launched()['cwd'])
        self.assertNotEqual(self.root, cwd)
        self.assertFalse(cwd.exists())
        self.assertFalse((self.root / 'cub.err').exists())

    def test_aggregate_pipe_limits(self):
        for mode in ('stdout_flood', 'stderr_flood', 'both_flood'):
            (self.root / 'mode').write_text(mode)
            self.assert_failure(self.run_cli(), 3)

    def wait_file(self, name):
        limit = time.monotonic() + 3
        while not (self.root / name).exists() and time.monotonic() < limit:
            time.sleep(.01)
        self.assertTrue((self.root / name).exists(), name)
        return self.root / name

    def assert_not_running(self, pid):
        limit = time.monotonic() + 2
        while time.monotonic() < limit:
            try:
                status = Path(f'/proc/{pid}/stat').read_text().split(') ', 1)[1].split()[0]
                if status == 'Z':
                    return
            except FileNotFoundError:
                return
            time.sleep(.01)
        self.fail(f'owned process {pid} remains running')

    def test_deadline_kills_leader_and_pipe_holding_descendant(self):
        (self.root / 'mode').write_text('fork')
        self.assert_failure(self.run_cli(extra=('--timeout', '.2')), 124)
        self.assert_not_running(self.launched()['pid'])
        self.assert_not_running(int((self.root / 'descendant').read_text()))

    def test_successful_leader_exit_cleans_up_pipe_holding_descendant(self):
        (self.root / 'mode').write_text('fork_exit')
        result = self.run_cli(extra=('--timeout', '1'))
        self.assertEqual(0, result.returncode, result.stderr)
        self.assert_not_running(int((self.root / 'descendant').read_text()))

    def test_signals_cancel_with_owned_group_cleanup(self):
        for sig in (signal.SIGTERM, signal.SIGINT):
            (self.root / 'mode').write_text('fork')
            (self.root / 'descendant').unlink(missing_ok=True)
            process = subprocess.Popen([*self.console, '--', '-udba', 'demodb'], stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE, env=self.environment)
            pid = int(self.wait_file('descendant').read_text())
            process.send_signal(sig)
            out, err = process.communicate(timeout=3)
            self.assert_failure(subprocess.CompletedProcess([], process.returncode, out, err), 130)
            self.assert_not_running(pid)
            self.assert_not_running(self.launched()['pid'])

    def test_stdin_is_deadline_bounded_and_cancellable_before_launch(self):
        for cancel in (False, True):
            process = subprocess.Popen([*self.console, '--timeout', '.2', '--request-stdin'],
                                       stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                       env=self.environment)
            if cancel:
                time.sleep(.1)
                process.send_signal(signal.SIGTERM)
            process.wait(timeout=3)
            out, err = process.communicate()
            self.assert_failure(subprocess.CompletedProcess([], process.returncode, out, err), 130 if cancel else 124)
            self.assertFalse((self.root / 'launch.json').exists())

    def start_large_export(self, timeout, *, merged=False):
        rows = ''.join(f'relation\tDBA\tDBA\ttable_{i:05d}\ttable_{i:05d}\tCLASS\n'
                       for i in range(5000))
        (self.root / 'catalog').write_text(HEADER + IDENTITY + rows)
        process = subprocess.Popen([*self.console, '--timeout', str(timeout), '--',
                                    '-psecret-password', 'demodb'], stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT if merged else subprocess.PIPE,
                                   env=self.environment)
        def cleanup():
            if process.poll() is None:
                process.kill()
            process.communicate(timeout=3)
        self.addCleanup(cleanup)
        self.assertTrue(select.select([process.stdout], [], [], 3)[0], 'no output started')
        return process

    def test_stalled_stdout_respects_timeout_and_cancellation_with_merged_stderr(self):
        for merged in (False, True):
            for cancel in (False, True):
                with self.subTest(merged=merged, cancel=cancel):
                    process = self.start_large_export(5 if cancel else .6, merged=merged)
                    if cancel:
                        process.send_signal(signal.SIGTERM)
                    self.assertEqual(130 if cancel else 124, process.wait(timeout=2))
                    out, err = process.communicate(timeout=2)
                    self.assertTrue(out)
                    self.assertNotIn(b'secret-password', out + (err or b''))

    def test_late_reader_cannot_turn_timeout_or_cancellation_into_success(self):
        for cancel in (False, True):
            with self.subTest(cancel=cancel):
                process = self.start_large_export(5 if cancel else .6)
                if cancel:
                    process.send_signal(signal.SIGTERM)
                time.sleep(.8 if not cancel else .2)
                out, err = process.communicate(timeout=3)
                self.assertEqual(130 if cancel else 124, process.returncode, err)
                self.assertTrue(out)
                self.assertNotIn(b'secret-password', out + err)

    def test_closed_stdout_fails_cleanly(self):
        process = subprocess.Popen([*self.console, '--', '-psecret-password', 'demodb'],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=self.environment)
        process.stdout.close()
        code = process.wait(timeout=3)
        err = process.stderr.read()
        process.stderr.close()
        self.assertEqual(3, code, err)
        self.assertLess(len(err), 200)
        self.assertNotIn(b'Traceback', err)
        self.assertNotIn(b'secret-password', err)

    def test_public_api_immutable_connection_and_cancellation(self):
        from dataclasses import FrozenInstanceError
        from threading import Event
        from cubrid_language.acquisition import AcquisitionError, Connection, acquire_schema, parse_connection, snapshot_json
        connection = parse_connection('csql -udba -psecret-password demodb')
        self.assertIsInstance(connection, Connection)
        self.assertNotIn('secret-password', repr(connection))
        self.assertEqual('secret-password', connection.password)
        with self.assertRaises(FrozenInstanceError):
            connection.user = 'other'
        cancelled = Event()
        cancelled.set()
        with self.assertRaises(AcquisitionError) as caught:
            acquire_schema(connection, executable=str(self.csql), cancelled=cancelled)
        self.assertEqual('cancelled', caught.exception.code)
        self.assertFalse((self.root / 'launch.json').exists())
        with self.assertRaises(AcquisitionError) as caught:
            parse_connection('csql -psecret-password "private-command')
        self.assertNotIn('private-command', str(caught.exception))
        self.assertNotIn('secret-password', str(caught.exception))

    def test_importable_acquisition_and_midflight_cancellation(self):
        from threading import Event, Timer
        from cubrid_language.acquisition import AcquisitionError, acquire_schema, parse_connection, snapshot_json
        connection = parse_connection(['-udba', 'demodb'])
        with patch.dict(os.environ, self.environment):
            schema = acquire_schema(connection, executable=str(self.csql))
            self.assertEqual('DBA', schema.user)
            self.assertEqual('demodb', json.loads(snapshot_json(schema))['database'])
            (self.root / 'mode').write_text('fork')
            cancelled = Event()
            timer = Timer(.2, cancelled.set)
            timer.start()
            try:
                with self.assertRaises(AcquisitionError) as caught:
                    acquire_schema(connection, executable=str(self.csql), cancelled=cancelled)
                self.assertEqual('cancelled', caught.exception.code)
            finally:
                timer.cancel()
                timer.join()
        self.assert_not_running(self.launched()['pid'])
        self.assert_not_running(int((self.root / 'descendant').read_text()))

    def test_public_api_invalid_values_and_serialized_output_limit(self):
        from cubrid_language import Relation, Schema
        from cubrid_language.acquisition import AcquisitionError, Connection, acquire_schema, snapshot_json
        for values in (dict(endpoint='private-command;secret-password'), dict(endpoint='demodb', user=''),
                       dict(endpoint='demodb', password='\x00'), dict(endpoint='demodb', user='\ud800')):
            with self.subTest(values=values), self.assertRaises(AcquisitionError):
                Connection(**values)
        for timeout in (True, None, float('nan'), float('inf'), -1, 0, 301, 10 ** 10000):
            with self.assertRaises(AcquisitionError) as caught:
                acquire_schema(Connection('demodb'), executable=str(self.csql), timeout=timeout)
            self.assertEqual('invalid-request', caught.exception.code)
        self.assertFalse((self.root / 'launch.json').exists())
        with self.assertRaises(AcquisitionError) as caught:
            snapshot_json(Schema('DBA', (Relation('DBA', '\x01' * (3 * 1024 * 1024), 'CLASS'),)))
        self.assertEqual('limit', caught.exception.code)

    def test_missing_executable_uses_fixed_failure(self):
        self.console = [*self.console[:-1], str(self.root / 'private-command-secret-password')]
        self.assert_failure(self.run_cli(), 3)
        self.assertFalse((self.root / 'launch.json').exists())

    def test_console_entry_point_is_registered(self):
        from importlib.metadata import distribution
        scripts = {entry.name: entry.value for entry in distribution('cubrid-language-tools').entry_points
                   if entry.group == 'console_scripts'}
        self.assertEqual('cubrid_language.schema_cli:main', scripts.get('cubrid-schema'))


if __name__ == '__main__':
    unittest.main()
