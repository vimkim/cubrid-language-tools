"""Mandatory actual-native LSP checks; absent artifacts or pygls must fail."""

import json
from pathlib import Path
import sys
import unittest

import pygls

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'lsp'))
from protocol_client import Client

ROOT = Path(__file__).resolve().parents[2]
BUILD = ROOT / 'native/parser-worker/build'


class NativeProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        manifest = json.loads((BUILD / 'manifest.json').read_bytes())
        if not (BUILD / 'parser-worker').is_file():
            raise FileNotFoundError(BUILD / 'parser-worker')
        cls.settings = {'cubrid': {'parserWorker': str(BUILD / 'parser-worker'),
                                   'runtimePrefix': manifest['runtimePrefix']}}

    def test_actual_native_syntax_and_unsupported_diagnostics_have_original_utf16_ranges(self):
        with Client() as client:
            client.initialize(self.settings, encodings=['utf-8', 'utf-16'])
            uri = client.open("SELECT '가😀';\r\nCREATE SERIAL s START WITH ;\r\nCREATE PROCEDURE p;")
            diagnostics = client.diagnostics(uri, 1)['diagnostics']
            self.assertEqual([d['code'] for d in diagnostics], ['CUBRID-S1001', 'CUBRID-U1002'])
            self.assertEqual(diagnostics[0]['range'], {'start': {'line': 0, 'character': 13},
                                                       'end': {'line': 1, 'character': 28}})
            self.assertEqual(diagnostics[0]['data'], {'category': 'syntax', 'rangePrecision': 'statement'})
            self.assertEqual([d['severity'] for d in diagnostics], [1, 2])
            self.assertEqual(diagnostics[1]['range']['end'], {'line': 2, 'character': 19})
            client.change(uri, "SELECT '가😀';", 2)
            self.assertEqual(client.diagnostics(uri, 2)['diagnostics'], [])

    def test_qualified_query_dml_and_unknown_profiles_use_shared_validator(self):
        with Client() as client:
            client.initialize(self.settings)
            uri = client.open('SELECT a.id FROM absent a WHERE a.id >= 3;')
            self.assertEqual(client.diagnostics(uri, 1)['diagnostics'], [])
            client.change(uri, 'INSERT INTO absent (id) VALUES (1);', 2)
            self.assertEqual(client.diagnostics(uri, 2)['diagnostics'], [])
            settings = {'cubrid': {**self.settings['cubrid'], 'profile': 'unknown-profile'}}
            client.send('workspace/didChangeConfiguration', {'settings': settings})
            client.change(uri, 'SELECT 1;', 3)
            self.assertEqual(client.diagnostics(uri, 3)['diagnostics'][0]['code'], 'CUBRID-U1001')

    def test_actual_native_same_line_non_bmp_error_span_uses_utf16(self):
        with Client() as client:
            client.initialize(self.settings)
            uri = client.open("SELECT '가😀';CREATE SERIAL s START WITH ;")
            diagnostic = client.diagnostics(uri, 1)['diagnostics'][0]
            self.assertEqual(diagnostic['code'], 'CUBRID-S1001')
            self.assertEqual(diagnostic['range'], {'start': {'line': 0, 'character': 13},
                                                   'end': {'line': 0, 'character': 41}})
