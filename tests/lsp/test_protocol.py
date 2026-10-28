"""Mandatory optional-adapter tests: missing pygls is a prerequisite failure."""

import unittest
import queue
import time

import pygls  # Fail visibly when the mandatory recipe lacks the optional extra.
from protocol_client import Client


class ProtocolTests(unittest.TestCase):
    def test_completion_rejects_noninteger_wire_positions_without_coercion_or_traceback(self):
        with Client() as client:
            client.initialize()
            uri = client.open('SEL')
            for line, character in ((False, 3), (0, True), (0, '3'), (0, 3.0)):
                with self.subTest(line=line, character=character):
                    self.assertEqual(client.completion(uri, line, character)['error']['code'], -32602)
            self.assertIn('SELECT', [i['label'] for i in client.completion(uri, 0, 3)['result']['items']])
            client.request('shutdown')
            client.send('exit')
            self.assertEqual(client.process.wait(timeout=3), 0)
            self.assertNotIn(b'Traceback', client.process.stderr.read())

    def test_open_and_change_reject_coerced_document_text_and_versions(self):
        invalid = (('version', True), ('version', '2'), ('version', 2.0),
                   ('text', 123), ('text', False), ('text', 3.0))
        with Client() as client:
            client.initialize()
            for index, (field, value) in enumerate(invalid):
                with self.subTest(operation='open', field=field, value=value):
                    uri = f'untitled:invalid-open-{index}'
                    document = {'uri': uri, 'languageId': 'cubrid', 'version': 1, 'text': 'SEL', field: value}
                    client.send('textDocument/didOpen', {'textDocument': document})
                    self.assertEqual(client.completion(uri, 0, 0)['result']['items'], [])
                    client.receive(lambda m: m.get('method') == 'window/logMessage'
                        and 'textDocument/didOpen' in m['params']['message'])
            uri = client.open('SELtail')
            for field, value in invalid:
                with self.subTest(operation='change', field=field, value=value):
                    document = {'uri': uri, 'version': 2}
                    change = {'text': 'FROM '}
                    if field == 'version':
                        document[field] = value
                    else:
                        change[field] = value
                    client.send('textDocument/didChange', {'textDocument': document, 'contentChanges': [change]})
                    self.assertIn('SELECT', [i['label'] for i in client.completion(uri, 0, 3)['result']['items']])
                    client.receive(lambda m: m.get('method') == 'window/logMessage'
                        and 'textDocument/didChange' in m['params']['message'])
            client.change(uri, 'FRtail', 2)
            self.assertIn('FROM', [i['label'] for i in client.completion(uri, 0, 2)['result']['items']])
            client.request('shutdown')
            client.send('exit')
            self.assertEqual(client.process.wait(timeout=3), 0)
            self.assertNotIn(b'Traceback', client.process.stderr.read())

    def test_initialize_negotiates_only_utf16_and_full_sync(self):
        for encodings in (None, ['utf-8', 'utf-16'], ['utf-32', 'utf-16'], ['unknown']):
            with self.subTest(encodings=encodings), Client() as client:
                reply = client.initialize(encodings=encodings)
                capabilities = reply['result']['capabilities']
                self.assertEqual(capabilities['positionEncoding'], 'utf-16')
                self.assertEqual(capabilities['textDocumentSync']['change'], 1)
                self.assertTrue(capabilities['textDocumentSync']['openClose'])
                self.assertIn('completionProvider', capabilities)
                self.assertEqual(capabilities['executeCommandProvider']['commands'], ['cubrid.reloadSchema'])
                self.assertNotIn('hoverProvider', capabilities)

    def test_completion_preserves_original_crlf_unicode_and_replaces_token_suffix(self):
        with Client() as client:
            client.initialize(encodings=['utf-8', 'utf-16'])
            uri = client.open('-- 가😀\r\nSELtail')
            result = client.completion(uri, 1, 3)['result']
            item = next(i for i in result['items'] if i['label'] == 'SELECT')
            self.assertEqual(item['textEdit'], {'range': {'start': {'line': 1, 'character': 0},
                                                         'end': {'line': 1, 'character': 7}},
                                                'newText': 'SELECT'})
            for line, character in ((0, 5), (0, 7), (2, 0), (1, 100), (-1, 0)):
                with self.subTest(line=line, character=character):
                    self.assertEqual(client.completion(uri, line, character)['error']['code'], -32602)
            client.change(uri, 'FRtail', version=2)
            item = next(i for i in client.completion(uri, 0, 2)['result']['items'] if i['label'] == 'FROM')
            self.assertEqual(item['textEdit']['range']['end'], {'line': 0, 'character': 6})

    def test_generic_sql_and_unopened_documents_do_not_activate_completion(self):
        with Client() as client:
            client.initialize()
            uri = client.open('SEL', language='sql')
            self.assertEqual(client.completion(uri, 0, 3)['result']['items'], [])
            self.assertEqual(client.completion('untitled:unopened', 0, 0)['result']['items'], [])

    def test_same_line_non_bmp_offsets_use_utf16_and_quoted_context_suppresses_items(self):
        with Client() as client:
            client.initialize(encodings=['utf-32', 'utf-8', 'utf-16'])
            uri = client.open("SELECT '가😀', SELtail")
            item = next(i for i in client.completion(uri, 0, 17)['result']['items'] if i['label'] == 'SELECT')
            self.assertEqual(item['textEdit']['range'], {'start': {'line': 0, 'character': 14},
                                                        'end': {'line': 0, 'character': 21}})
            self.assertEqual(client.completion(uri, 0, 9)['result']['items'], [])

    def test_reopening_with_a_different_language_deactivates_existing_cubrid_document(self):
        with Client() as client:
            client.initialize()
            uri = client.open('SEL')
            self.assertTrue(client.completion(uri, 0, 3)['result']['items'])
            client.open('SEL', uri=uri, language='sql', version=2)
            self.assertEqual(client.completion(uri, 0, 3)['result']['items'], [])
            self.assertEqual(client.diagnostics(uri)['diagnostics'], [])

    def test_full_sync_rejects_ranged_changes_without_mutating_source(self):
        with Client() as client:
            client.initialize()
            uri = client.open('SELtail')
            client.send('textDocument/didChange', {'textDocument': {'uri': uri, 'version': 2},
                'contentChanges': [{'range': {'start': {'line': 0, 'character': 1},
                                              'end': {'line': 0, 'character': 2}}, 'text': 'X'}]})
            reply = client.completion(uri, 0, 3)
            self.assertIn('SELECT', [i['label'] for i in reply['result']['items']])

    def test_missing_runtime_diagnostics_are_versioned_debounced_and_cleared_on_close(self):
        with Client() as client:
            client.initialize()
            started = time.monotonic()
            uri = client.open('SEL')
            self.assertIn('SELECT', [i['label'] for i in client.completion(uri, 0, 3)['result']['items']])
            client.change(uri, 'SELECT 1;', version=2)
            result = client.diagnostics(uri, 2)
            self.assertGreaterEqual(time.monotonic() - started, 0.24)
            self.assertEqual(result['diagnostics'][0]['code'], 'CUBRID-T1001')
            self.assertEqual(result['diagnostics'][0]['severity'], 1)
            client.send('textDocument/didClose', {'textDocument': {'uri': uri}})
            self.assertEqual(client.diagnostics(uri)['diagnostics'], [])
            self.assertEqual(client.completion(uri, 0, 0)['result']['items'], [])
            with self.assertRaises(queue.Empty):
                client.diagnostics(uri, 1, timeout=0.35)

    def test_non_cubrid_documents_never_publish_diagnostics(self):
        with Client() as client:
            client.initialize()
            uri = client.open('SELECT 1;', language='sql')
            client.change(uri, 'SELECT 2;')
            client.send('textDocument/didClose', {'textDocument': {'uri': uri}})
            with self.assertRaises(queue.Empty):
                client.diagnostics(uri, timeout=0.4)

    def test_invalid_unicode_and_nul_are_visible_input_failures(self):
        with Client() as client:
            client.initialize()
            for index, text in enumerate(('SELECT \0;', '\ud800')):
                uri = client.open(text, uri=f'untitled:invalid-{index}')
                diagnostic = client.diagnostics(uri, 1)['diagnostics'][0]
                self.assertEqual(diagnostic['code'], 'CUBRID-T1003')


if __name__ == '__main__':
    unittest.main()
