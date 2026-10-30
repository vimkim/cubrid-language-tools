import json
import os
from pathlib import Path
import tempfile
import unittest
import time

import pygls
from protocol_client import Client


def reload(client):
    return client.request('workspace/executeCommand', {'command': 'cubrid.reloadSchema'})


def labels(client, uri):
    return [i['label'] for i in client.completion(uri, 0, len('SELECT * FROM '))['result']['items']]


def snapshot(path, name):
    path.write_text(json.dumps({'schemaVersion': 1, 'user': 'dba', 'relations': [
        {'owner': 'dba', 'name': name, 'kind': 'CLASS', 'columns': ['가😀']}]}), encoding='utf-8')


class ConfigurationTests(unittest.TestCase):
    def test_snapshot_load_reload_stale_and_explicit_clear(self):
        with tempfile.TemporaryDirectory() as directory, Client(cwd=directory) as client:
            path = Path(directory) / 'catalog.json'
            snapshot(path, 'First가😀')
            client.initialize({'cubrid': {'schemaSnapshot': str(path)}})
            uri = client.open('SELECT * FROM ')
            self.assertIn('[First가😀]', labels(client, uri))
            snapshot(path, 'Second')
            self.assertIn('[First가😀]', labels(client, uri))
            state = reload(client)['result'][0]
            self.assertFalse(state['stale'])
            self.assertIn('[Second]', labels(client, uri))
            path.write_text('invalid')
            state = reload(client)['result'][0]
            self.assertTrue(state['stale'])
            self.assertIn('stale', state['availability'])
            self.assertIn('[Second]', labels(client, uri))
            client.receive(lambda m: m.get('method') == 'window/logMessage' and 'stale' in m['params']['message'])
            client.send('workspace/didChangeConfiguration', {'settings': {'cubrid': {'schemaSnapshot': None}}})
            self.assertNotIn('[Second]', labels(client, uri))
            self.assertFalse(reload(client)['result'][0]['schemaAvailable'])

    def test_config_profile_mode_filename_and_editor_precedence(self):
        with tempfile.TemporaryDirectory() as directory, Client(cwd=directory) as client:
            root = Path(directory)
            config = root / '.cubrid-language.json'
            config.write_text('{"profile":"project-profile","scriptMode":"csql","schemaSnapshot":"catalog.json"}')
            snapshot(root / 'catalog.json', 'ProjectTable')
            client.initialize()
            file_uri = client.open('SELECT * FROM ', (root / 'file.sql').as_uri())
            untitled_uri = client.open('SELECT * FROM ', 'untitled:sql-default')
            states = {s['uri']: s for s in reload(client)['result']}
            self.assertEqual((states[file_uri]['profile'], states[file_uri]['scriptMode']), ('project-profile', 'csql'))
            self.assertEqual(states[untitled_uri]['scriptMode'], 'sql')
            self.assertIn('ProjectTable', labels(client, file_uri))
            client.send('workspace/didChangeConfiguration', {'settings': {'cubrid': {
                'profile': 'editor-profile', 'scriptMode': 'sql', 'schemaSnapshot': None}}})
            states = reload(client)['result']
            self.assertTrue(all((s['profile'], s['scriptMode']) == ('editor-profile', 'sql') for s in states))
            config.unlink()
            client.send('workspace/didChangeConfiguration', {'settings': {'cubrid': {}}})
            client.open('', (root / 'filename.CSQL').as_uri())
            states = {s['uri']: s for s in reload(client)['result']}
            self.assertEqual(states[(root / 'filename.CSQL').as_uri()]['scriptMode'], 'csql')
            self.assertEqual(states[file_uri]['scriptMode'], 'sql')

    def test_bad_project_and_trusted_configuration_are_visible(self):
        with tempfile.TemporaryDirectory() as directory, Client(cwd=directory) as client:
            root = Path(directory)
            (root / '.cubrid-language.json').write_text('{"parserWorker":"/bin/false"}')
            client.initialize()
            uri = client.open('SEL', (root / 'file.sql').as_uri())
            self.assertEqual(client.diagnostics(uri)['diagnostics'][0]['code'], 'CUBRID-T1003')
            (root / '.cubrid-language.json').unlink()
            client.send('workspace/didChangeConfiguration', {'settings': {'cubrid': {'parserWorker': '/bin/false'}}})
            self.assertEqual(client.diagnostics(uri)['diagnostics'][0]['code'], 'CUBRID-T1003')

    def test_missing_configured_snapshot_is_visible_but_keywords_work(self):
        with tempfile.TemporaryDirectory() as directory, Client(cwd=directory) as client:
            client.initialize({'cubrid': {'schemaSnapshot': 'missing.json'}})
            uri = client.open('SEL')
            self.assertIn('SELECT', [i['label'] for i in client.completion(uri, 0, 3)['result']['items']])
            state = reload(client)['result'][0]
            self.assertFalse(state['schemaAvailable'])
            self.assertIn('unavailable', state['availability'])
            client.receive(lambda m: m.get('method') == 'window/logMessage' and 'unavailable' in m['params']['message'])

    def test_reload_reports_configured_schema_even_when_the_file_is_missing(self):
        with tempfile.TemporaryDirectory() as directory, Client(cwd=directory) as client:
            root = Path(directory)
            client.initialize()
            client.open('SEL', (root / 'file.sql').as_uri())
            state = reload(client)['result'][0]
            self.assertIs(False, state['schemaConfigured'])
            self.assertIs(False, state['schemaAvailable'])
            config = root / '.cubrid-language.json'
            config.write_text('{"schemaSnapshot":"missing.json"}')
            state = reload(client)['result'][0]
            self.assertIs(True, state['schemaConfigured'])
            self.assertIs(False, state['schemaAvailable'])
            client.send('workspace/didChangeConfiguration', {'settings': {'cubrid': {'schemaSnapshot': None}}})
            self.assertIs(False, reload(client)['result'][0]['schemaConfigured'])
            client.send('workspace/didChangeConfiguration', {'settings': {'cubrid': {'schemaSnapshot': 'also-missing.json'}}})
            self.assertIs(True, reload(client)['result'][0]['schemaConfigured'])

    def test_invalid_trusted_worker_paths_and_setting_types_are_configuration_failures(self):
        invalid = ({'parserWorker': '/bad\0path', 'runtimePrefix': '/runtime'},
                   {'parserWorker': '/bad\ud800path', 'runtimePrefix': '/runtime'},
                   {'parserWorker': '/worker', 'runtimePrefix': '/runtime', 'workerTimeout': False},
                   {'scriptMode': None}, {'profile': None}, [], {'unknownSetting': True})
        with Client() as client:
            client.initialize()
            uri = client.open('SEL')
            for index, values in enumerate(invalid, start=2):
                with self.subTest(values=values):
                    client.send('workspace/didChangeConfiguration', {'settings': {'cubrid': values}})
                    client.change(uri, 'SEL', index)
                    self.assertEqual(client.diagnostics(uri, index)['diagnostics'][0]['code'], 'CUBRID-T1003')

    def test_protocol_request_cancellation_uses_request_cancelled_error(self):
        with tempfile.TemporaryDirectory() as directory, Client(cwd=directory) as client:
            path = Path(directory) / 'catalog.json'
            snapshot(path, 'Original')
            client.initialize({'cubrid': {'schemaSnapshot': str(path)}})
            client.open('SEL')
            client.completion('untitled:example', 0, 3)
            path.unlink()
            os.mkfifo(path)
            ident = client.send('workspace/executeCommand', {'command': 'cubrid.reloadSchema'}, request=True)
            deadline = time.monotonic() + 3
            while True:
                try:
                    writer = os.open(path, os.O_WRONLY | os.O_NONBLOCK)
                    break
                except OSError:
                    if time.monotonic() > deadline:
                        self.fail('snapshot reload never started')
                    time.sleep(0.01)
            try:
                client.send('$/cancelRequest', {'id': ident})
                self.assertEqual(client.response(ident)['error']['code'], -32800)
            finally:
                os.close(writer)
                path.unlink()
                snapshot(path, 'Restored')
            self.assertIn('result', reload(client))
