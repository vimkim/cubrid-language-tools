"""Mandatory framed LSP parity with the actual qualified script Validator."""

import json
from pathlib import Path
import sys
import tempfile
import unittest

import pygls

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'lsp'))
from protocol_client import Client

from cubrid_language.validation import PROFILE, Validator, WorkerConfig

ROOT = Path(__file__).resolve().parents[2]
BUILD = ROOT / 'native/parser-worker/build'


class NativeScriptProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        manifest = json.loads((BUILD / 'manifest.json').read_bytes())
        if not (BUILD / 'parser-worker').is_file():
            raise FileNotFoundError(BUILD / 'parser-worker')
        cls.config = WorkerConfig(BUILD / 'parser-worker', Path(manifest['runtimePrefix']))
        cls.settings = {'cubrid': {'parserWorker': str(cls.config.executable),
                                   'runtimePrefix': str(cls.config.runtime_prefix)}}

    def test_actual_script_diagnostics_match_library_codes_and_original_utf16_ranges(self):
        text = ";help\r\nSELECT '가😀';\r\n;read other.sql\r\nCREATE SERIAL s START WITH ;\r\n;exit"
        with tempfile.TemporaryDirectory() as directory, Client() as client:
            client.initialize(self.settings)
            uri = client.open(text, uri=(Path(directory) / 'script.csql').as_uri())
            diagnostics = client.diagnostics(uri, 1)['diagnostics']
            with Validator(self.config) as validator:
                library = validator.validate(text, PROFILE, 'csql')
            self.assertEqual([d['code'] for d in diagnostics], [d.code for d in library.diagnostics])
            self.assertEqual([d['range'] for d in diagnostics], [
                {'start': {'line': 2, 'character': 0}, 'end': {'line': 3, 'character': 0}},
                {'start': {'line': 3, 'character': 0}, 'end': {'line': 3, 'character': 28}}])
            self.assertEqual([d['data']['rangePrecision'] for d in diagnostics], ['statement', 'statement'])
            self.assertEqual([d['severity'] for d in diagnostics], [2, 1])
            client.change(uri, ";help \t\r\nSELECT '가😀;';\r\n;exit\t\r\n;autocommit\t on \t\r\nSELECT 2", 2)
            self.assertEqual(client.diagnostics(uri, 2)['diagnostics'], [])

    def test_pending_sql_procedures_and_unterminated_tokens_keep_shared_classification(self):
        with tempfile.TemporaryDirectory() as directory, Client() as client:
            client.initialize(self.settings)
            uri = client.open('SELECT\n;help\n1;', uri=(Path(directory) / 'script.csql').as_uri())
            for version, text, codes in (
                (1, None, ['CUBRID-U1002']),
                (2, 'SELECT (\r\n;exit\r\n1);', ['CUBRID-U1002']),
                (3, 'CREATE PROCEDURE p() AS BEGIN SELECT 1; SELECT 2; END;', ['CUBRID-U1002']),
                (4, ";help\r\nSELECT '가😀\r\n;exit", ['CUBRID-S1001']),
                (5, "CREATE PROCEDURE p() AS BEGIN SELECT 'open", ['CUBRID-S1001', 'CUBRID-U1002'])):
                with self.subTest(version=version):
                    if text is not None:
                        client.change(uri, text, version)
                    diagnostics = client.diagnostics(uri, version)['diagnostics']
                    self.assertEqual([d['code'] for d in diagnostics], codes)
                    if version == 4:
                        self.assertEqual(diagnostics[0]['range'], {
                            'start': {'line': 1, 'character': 0}, 'end': {'line': 2, 'character': 5}})

    def test_commands_only_still_require_profile_worker_and_explicit_csql_mode(self):
        with Client() as client:
            client.initialize(self.settings)
            uri = client.open(';help\n;exit', uri='untitled:script')
            self.assertTrue(client.diagnostics(uri, 1)['diagnostics'])
            client.send('workspace/didChangeConfiguration', {'settings': {
                'cubrid': {**self.settings['cubrid'], 'scriptMode': 'csql'}}})
            client.change(uri, ';help\n;exit', 2)
            self.assertEqual(client.diagnostics(uri, 2)['diagnostics'], [])
            client.send('workspace/didChangeConfiguration', {'settings': {
                'cubrid': {**self.settings['cubrid'], 'scriptMode': 'csql', 'profile': 'unknown-profile'}}})
            client.change(uri, ';autocommit off', 3)
            self.assertEqual([d['code'] for d in client.diagnostics(uri, 3)['diagnostics']], ['CUBRID-U1001'])
            client.change(uri, "BEGIN\n'open", 4)
            self.assertEqual([d['code'] for d in client.diagnostics(uri, 4)['diagnostics']], ['CUBRID-U1001'])
            client.send('workspace/didChangeConfiguration', {'settings': {
                'cubrid': {'parserWorker': '/nonexistent/script-worker',
                           'runtimePrefix': str(self.config.runtime_prefix), 'scriptMode': 'csql'}}})
            client.change(uri, ';help', 5)
            self.assertEqual([d['code'] for d in client.diagnostics(uri, 5)['diagnostics']], ['CUBRID-T1001'])
