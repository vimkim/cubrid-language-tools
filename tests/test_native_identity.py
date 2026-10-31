import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from cubrid_language.validation import NativeWorker, PROFILE, Validator, WorkerConfig
from cubrid_language.validation.profiles import qualified_identity


class NativeIdentityTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name) / 'native "가"\nassets'
        self.root.mkdir()
        self.runtime = self.root / 'trusted runtime'
        self.log = self.root / 'requests.jsonl'

    def worker(self, changes=None, *, omit=(), response=None):
        executable = self.root / 'worker'
        manifest = self.root / 'manifest.json'
        manifest.write_text('{}')
        digest = hashlib.sha256(manifest.read_bytes()).hexdigest()
        identity = {'status': 'ready', 'manifestDigest': digest,
                    **qualified_identity(PROFILE, self.runtime), **(changes or {})}
        for field in omit:
            identity.pop(field)
        if response is not None:
            identity = response
        result = {'status': 'valid', 'profile': PROFILE, 'coverage': 'complete',
                  'diagnostics': [], 'statementKinds': ['PT_SELECT'], 'manifestDigest': digest,
                  'syntaxSettingsUnchanged': True,
                  'coverageDecisions': [{'start': 0, 'end': 9, 'admitted': True}],
                  'nativeObservations': [{'hasTree': True, 'treeCount': 1, 'hasInternalError': False,
                      'hasError': False, 'errorCount': 0, 'nativeErrorId': 0, 'partialStackCount': 0}]}
        executable.write_text(
            f'#!{sys.executable}\n'
            'import json, os, pathlib, sys\n'
            f'identity={identity!r}\nresult={result!r}\nlog=pathlib.Path({str(self.log)!r})\n'
            'for line in sys.stdin:\n'
            ' request=json.loads(line)\n'
            " with log.open('a') as stream:\n"
            "  stream.write(json.dumps({'method':request['method'],'pid':os.getpid()})+'\\n')\n"
            " value=dict(identity if request['method']=='initialize' else result)\n"
            " if request['method']=='shutdown': value={'status':'closed'}\n"
            " value.update(protocolVersion=1,id=request['id'])\n"
            ' print(json.dumps(value),flush=True)\n'
            " if request['method']=='shutdown': break\n")
        executable.chmod(0o755)
        return WorkerConfig(executable, self.runtime, manifest)

    def requests(self):
        return [json.loads(line) for line in self.log.read_text().splitlines()]

    def test_stale_coverage_warning_explains_values_paths_and_recovery_without_parsing(self):
        stale = 'bounded-query-dml-schema-engineer-v3'
        config = self.worker({'coverageRevision': stale, 'unrelated': 'PRIVATE-RESPONSE-DATA'})
        for mode in ('sql', 'csql'):
            with self.subTest(mode=mode), Validator(config) as validator:
                result = validator.validate("SELECT 'PRIVATE-DOCUMENT-CONTENT';", PROFILE, mode)
                self.assertEqual((result.status, result.coverage, result.profile), ('unsupported', 'none', PROFILE))
                self.assertEqual(len(result.diagnostics), 1)
                diagnostic = result.diagnostics[0]
                self.assertEqual((diagnostic.code, diagnostic.category, diagnostic.severity),
                                 ('CUBRID-U1001', 'unsupported', 'warning'))
                expected = qualified_identity(PROFILE, self.runtime)['coverageRevision']
                self.assertIn(f'coverageRevision: expected {json.dumps(expected)}, actual {json.dumps(stale)}',
                              diagnostic.message)
                self.assertIn(f'worker={json.dumps(str(config.executable))}', diagnostic.message)
                self.assertIn(f'manifest={json.dumps(str(config.manifest))}', diagnostic.message)
                self.assertIn('Rebuild and qualify', diagnostic.message)
                self.assertIn('same core checkout', diagnostic.message)
                self.assertIn('runtime', diagnostic.message)
                self.assertIn('Restart', diagnostic.message)
                self.assertNotIn('PRIVATE-', diagnostic.message)
                self.assertNotIn('\n', diagnostic.message)
                repeated = validator.validate('SELECT 1;', PROFILE, mode)
                self.assertEqual((repeated.status, repeated.coverage, repeated.diagnostics[0].message),
                                 (result.status, result.coverage, diagnostic.message))
        requests = self.requests()
        self.assertEqual([request['method'] for request in requests], ['initialize', 'initialize'])
        for request in requests:
            with self.assertRaises(ChildProcessError):
                os.waitpid(request['pid'], os.WNOHANG)

    def test_multiple_identity_fields_and_nested_settings_have_deterministic_details(self):
        settings = qualified_identity(PROFILE, self.runtime)['settings']
        del settings['intl_collation']
        settings.update(ansi_quotes=False, extra_setting='line\n"quote"')
        changes = {'sourceCommit': 'old-source', 'nativeVersion': 'old-version', 'settings': settings}
        messages = []
        reordered = {**dict(reversed(list(changes.items()))), 'settings': dict(reversed(list(settings.items())))}
        for values in (changes, reordered):
            with NativeWorker(self.worker(values)) as worker:
                result = worker.parse('SELECT 1;')
            self.assertEqual(result.status, 'unsupported')
            message = result.diagnostics[0].message
            expected_details = [
                'nativeVersion: expected "11.5.0.2704-cc94778", actual "old-version"',
                'settings["ansi_quotes"]: expected true, actual false',
                'settings["extra_setting"]: expected <missing>, actual "line\\n\\"quote\\""',
                'settings["intl_collation"]: expected "utf8_bin", actual <missing>',
                'sourceCommit: expected "cc947788d3b7dc402f46192d0f3299ddcc8563ba", actual "old-source"',
            ]
            for detail in expected_details:
                self.assertIn(detail, message)
            self.assertEqual([message.index(detail) for detail in expected_details],
                             sorted(message.index(detail) for detail in expected_details))
            messages.append(message)
        self.assertEqual(messages[0], messages[1])
        self.assertEqual([request['method'] for request in self.requests()], ['initialize', 'initialize'])

    def test_matching_identity_still_initializes_and_parses(self):
        with NativeWorker(self.worker({'unrelated': 'ignored'})) as worker:
            identity = worker.initialize()
            self.assertEqual(identity['coverageRevision'], qualified_identity(PROFILE, self.runtime)['coverageRevision'])
            result = worker.parse('SELECT 1;')
            self.assertEqual((result.status, result.coverage, result.diagnostics), ('valid', 'complete', ()))
        self.assertEqual([request['method'] for request in self.requests()], ['initialize', 'parse', 'shutdown'])

    def test_large_identity_values_and_many_differences_are_explicitly_bounded(self):
        settings = qualified_identity(PROFILE, self.runtime)['settings']
        settings.update({f'extra_{index:02}': True for index in range(40)})
        config = self.worker({'nativeVersion': 'x' * 4096 + 'VALUE-END-MUST-NOT-APPEAR', 'settings': settings})
        with NativeWorker(config) as worker:
            result = worker.parse('SELECT 1;')
        self.assertEqual(result.status, 'unsupported')
        message = result.diagnostics[0].message
        self.assertIn('truncated JSON value, first 1024 characters:', message)
        self.assertIn('additional mismatched fields omitted', message)
        self.assertNotIn('VALUE-END-MUST-NOT-APPEAR', message)
        self.assertIn(f'worker={json.dumps(str(config.executable))}', message)
        self.assertIn('Restart', message)

    def test_identity_rejection_taxonomy_remains_distinct(self):
        for changes, omit, response, code in (
            ({'testOnly': True}, (), None, 'CUBRID-U1001'),
            ({'testOnly': 0}, (), None, 'CUBRID-T1002'),
            ({'settings': []}, (), None, 'CUBRID-T1002'),
            ({}, ('coverageRevision',), None, 'CUBRID-T1002'),
            ({'manifestDigest': 'a' * 64}, (), None, 'CUBRID-T1002'),
            ({}, (), {'status': 'tool-error', 'code': 'CUBRID-T1001', 'message': 'native input unavailable'}, 'CUBRID-T1001'),
            ({}, (), {'status': 'tool-error', 'code': 'CUBRID-T1002', 'message': 'manifest tampered'}, 'CUBRID-T1002'),
        ):
            with self.subTest(changes=changes, omit=omit, response=response):
                with NativeWorker(self.worker(changes, omit=omit, response=response)) as worker:
                    result = worker.parse('SELECT 1;')
                self.assertEqual(result.diagnostics[0].code, code)
                self.assertEqual(result.status, 'unsupported' if code == 'CUBRID-U1001' else 'tool-error')
        config = self.worker()
        config.manifest.unlink()
        with NativeWorker(config) as worker:
            self.assertEqual(worker.parse('SELECT 1;').diagnostics[0].code, 'CUBRID-T1001')
        self.assertEqual({request['method'] for request in self.requests()}, {'initialize'})

    def test_detailed_warning_survives_cli_json_transport(self):
        config = self.worker({'coverageRevision': 'stale-v3'})
        result = subprocess.run(
            [sys.executable, '-m', 'cubrid_language.cli', '--format', 'json',
             '--parser-worker', str(config.executable), '--runtime-prefix', str(config.runtime_prefix), '-'],
            input=b'SELECT 1;', capture_output=True, cwd=self.root, timeout=10)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual(result.stderr, b'')
        document = json.loads(result.stdout)['documents'][0]
        self.assertEqual((document['status'], document['coverage']), ('unsupported', 'none'))
        diagnostic = document['diagnostics'][0]
        self.assertEqual((diagnostic['code'], diagnostic['severity']), ('CUBRID-U1001', 'warning'))
        self.assertIn('coverageRevision: expected "bounded-query-dml-schema-engineer-ordered-v4", actual "stale-v3"',
                      diagnostic['message'])
        self.assertIn(f'worker={json.dumps(str(config.executable))}', diagnostic['message'])
        self.assertIn('Restart', diagnostic['message'])
        self.assertEqual([request['method'] for request in self.requests()], ['initialize'])
