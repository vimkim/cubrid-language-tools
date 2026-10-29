import json
import queue
import tempfile
import time
import unittest

import pygls
from protocol_client import Client
from worker_fixture import event, wait_reaped, worker


class ResponsivenessTests(unittest.TestCase):
    def test_native_crlf_interior_ranges_become_visible_tool_failures(self):
        with tempfile.TemporaryDirectory() as directory, Client() as client:
            settings, log = worker(directory, bad_range=True)
            client.initialize(settings)
            uri = client.open('\r\nSELECT 1;')
            diagnostic = client.diagnostics(uri)['diagnostics'][0]
            self.assertEqual(diagnostic['code'], 'CUBRID-T1002')
            self.assertIn('range', diagnostic['message'])

    def test_completion_during_worker_start_and_close_reaps_owned_child(self):
        with tempfile.TemporaryDirectory() as directory, Client() as client:
            settings, log = worker(directory, initialize_delay=3)
            client.initialize(settings)
            uri = client.open('SEL')
            pid = event(log, 'initialize')['pid']
            start = time.monotonic()
            self.assertIn('SELECT', [i['label'] for i in client.completion(uri, 0, 3)['result']['items']])
            self.assertLess(time.monotonic() - start, .5)
            client.send('textDocument/didClose', {'textDocument': {'uri': uri}})
            self.assertEqual(client.diagnostics(uri)['diagnostics'], [])
            wait_reaped(pid)
            with self.assertRaises(queue.Empty):
                client.diagnostics(uri, timeout=.35)

    def test_superseded_validation_cannot_publish_or_replace_current_version(self):
        with tempfile.TemporaryDirectory() as directory, Client() as client:
            settings, log = worker(directory, parse_delay=.7)
            client.initialize(settings)
            uri = client.open('SELECT 1;')
            pid = event(log, 'parse')['pid']
            client.change(uri, 'SELECT 2;', 2)
            client.change(uri, 'SELECT 3;', 3)
            wait_reaped(pid)
            result = client.diagnostics(uri, 3)
            self.assertEqual(result['diagnostics'], [])
            client.change(uri, 'SELECT 9;', 2)
            with self.assertRaises(queue.Empty):
                client.diagnostics(uri, 1, timeout=.35)
            with self.assertRaises(queue.Empty):
                client.diagnostics(uri, 2, timeout=.1)

    def test_shutdown_cancels_active_parse_and_has_no_late_diagnostics(self):
        with tempfile.TemporaryDirectory() as directory, Client() as client:
            settings, log = worker(directory, parse_delay=10)
            client.initialize(settings)
            client.open('SELECT 1;')
            pid = event(log, 'parse')['pid']
            start = time.monotonic()
            self.assertIn('SELECT', [i['label'] for i in client.completion('untitled:example', 0, 3)['result']['items']])
            self.assertLess(time.monotonic() - start, .5)
            start = time.monotonic()
            self.assertIn('result', client.request('shutdown'))
            self.assertLess(time.monotonic() - start, .8)
            wait_reaped(pid)
            client.send('exit')
            self.assertEqual(client.process.wait(timeout=3), 0)

    def test_cancelled_queued_documents_cannot_start_workers_later(self):
        with tempfile.TemporaryDirectory() as directory, Client() as client:
            settings, log = worker(directory, initialize_delay=10)
            client.initialize(settings)
            uris = [client.open('SELECT 1;', f'untitled:queue-{i}') for i in range(8)]
            event(log, 'initialize', count=4)
            for uri in reversed(uris):
                client.send('textDocument/didClose', {'textDocument': {'uri': uri}})
                self.assertEqual(client.diagnostics(uri)['diagnostics'], [])
            client.request('shutdown')
            events = [json.loads(line) for line in log.read_text().splitlines()]
            starts = [e for e in events if e['method'] == 'initialize']
            self.assertEqual(len(starts), 4)
            for value in starts:
                wait_reaped(value['pid'])

    def test_shutdown_gates_all_queued_workers_before_reaping_active_children(self):
        with tempfile.TemporaryDirectory() as directory, Client() as client:
            settings, log = worker(directory, initialize_delay=10)
            client.initialize(settings)
            for index in range(8):
                client.open('SELECT 1;', f'untitled:shutdown-queue-{index}')
            event(log, 'initialize', count=4)
            self.assertIn('result', client.request('shutdown'))
            starts = [json.loads(line) for line in log.read_text().splitlines()]
            self.assertEqual(len(starts), 4)
            for value in starts:
                wait_reaped(value['pid'])

    def test_failing_worker_is_visible_without_breaking_completion(self):
        with tempfile.TemporaryDirectory() as directory, Client() as client:
            settings, log = worker(directory, crash=True)
            client.initialize(settings)
            uri = client.open('SEL')
            self.assertEqual(client.diagnostics(uri)['diagnostics'][0]['code'], 'CUBRID-T1002')
            self.assertIn('SELECT', [i['label'] for i in client.completion(uri, 0, 3)['result']['items']])
            wait_reaped(event(log, 'initialize')['pid'])

    def test_exit_without_shutdown_and_eof_reap_owned_worker(self):
        for eof in (False, True):
            with self.subTest(eof=eof), tempfile.TemporaryDirectory() as directory, Client() as client:
                settings, log = worker(directory, parse_delay=10)
                client.initialize(settings)
                client.open('SELECT 1;')
                pid = event(log, 'parse')['pid']
                if eof:
                    client.process.stdin.close()
                else:
                    client.send('exit')
                self.assertEqual(client.process.wait(timeout=3), 1)
                wait_reaped(pid)

    def test_configuration_change_cancels_owned_old_worker(self):
        with tempfile.TemporaryDirectory() as directory, Client() as client:
            settings, log = worker(directory, initialize_delay=10)
            client.initialize(settings)
            uri = client.open('SELECT 1;')
            pid = event(log, 'initialize')['pid']
            client.send('workspace/didChangeConfiguration', {'settings': {'cubrid': {}}})
            self.assertEqual(client.diagnostics(uri)['diagnostics'][0]['code'], 'CUBRID-T1001')
            wait_reaped(pid)

class HintCancellationTests(unittest.TestCase):
    def test_superseded_warning_never_publishes(self):
        with tempfile.TemporaryDirectory() as directory, Client() as client:
            settings, log = worker(directory, parse_delay=.7)
            client.initialize(settings)
            uri = client.open('SELECT /*+ BOGUS */ 1;')
            pid = event(log, 'parse')['pid']
            client.change(uri, 'SELECT 1;', 2)
            wait_reaped(pid)
            self.assertEqual(client.diagnostics(uri, 2)['diagnostics'], [])
            with self.assertRaises(queue.Empty):
                client.diagnostics(uri, 1, timeout=.4)
