import json
from pathlib import Path
import subprocess
import sys
import unittest

from cubrid_language.validation import PROFILE, Validator, WorkerConfig


class ShowHintCliTests(unittest.TestCase):
    def test_ordered_validator_and_cli_keep_original_unicode_crlf_ranges(self):
        build = Path(__file__).resolve().parents[2] / 'native/parser-worker/build'
        manifest = json.loads((build / 'manifest.json').read_text())
        config = WorkerConfig(build / 'parser-worker', Path(manifest['runtimePrefix']))
        text = "SELECT /*+ ORDERED */ '가😀';\r\nSELECT /*+ ORDERED */ ,;\r\nSELECT /*+ ORDERED(t) */ 1;"
        with Validator(config) as validator:
            result = validator.validate(text, PROFILE, 'sql')
            self.assertEqual((result.status, result.coverage), ('syntax-error', 'partial'))
            self.assertEqual([(d.code, d.span.start, d.span.end) for d in result.diagnostics],
                             [('CUBRID-S1001', 27, 53), ('CUBRID-U1002', 53, 82)])
            self.assertTrue(all(d.range_precision == 'statement' for d in result.diagnostics))
            self.assertEqual(validator.validate('SELECT /*+ ORDERED */ 1;', PROFILE, 'sql').status, 'valid')
        process = subprocess.run([sys.executable, '-m', 'cubrid_language.cli', '--format', 'json',
                                  '--parser-worker', str(config.executable),
                                  '--runtime-prefix', str(config.runtime_prefix), '-'],
                                 input=text, capture_output=True, text=True, timeout=15)
        self.assertEqual(process.returncode, 1, process.stderr)
        document = json.loads(process.stdout)['documents'][0]
        self.assertEqual((document['status'], document['coverage']), (result.status, result.coverage))
        self.assertEqual(document['diagnostics'], [d.to_dict() for d in result.diagnostics])

    def test_cli_matches_validator_with_unsupported_native_coverage(self):
        build = Path(__file__).resolve().parents[2] / 'native/parser-worker/build'
        manifest = json.loads((build / 'manifest.json').read_text())
        worker = (build / 'parser-worker').resolve()
        runtime = Path(manifest['runtimePrefix'])
        text = "SELECT '😀', /*+ BOGUS */ 1;"
        with Validator(WorkerConfig(worker, runtime)) as validator:
            expected = validator.validate(text, PROFILE, 'sql')
        process = subprocess.run([sys.executable, '-m', 'cubrid_language.cli', '--format', 'json',
                                  '--parser-worker', str(worker), '--runtime-prefix', str(runtime), '-'],
                                 input=text, capture_output=True, text=True, timeout=15)
        self.assertEqual(process.returncode, 2, process.stderr)
        document = json.loads(process.stdout)['documents'][0]
        self.assertEqual(document['status'], expected.status)
        self.assertEqual(document['diagnostics'], [d.to_dict() for d in expected.diagnostics])
        self.assertEqual([d['code'] for d in document['diagnostics']], ['CUBRID-U1002', 'CUBRID-A1001'])
