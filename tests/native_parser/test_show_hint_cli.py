import json
from pathlib import Path
import subprocess
import sys
import unittest

from cubrid_language.validation import PROFILE, Validator, WorkerConfig


class ShowHintCliTests(unittest.TestCase):
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
