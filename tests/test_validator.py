from concurrent.futures import ThreadPoolExecutor
import hashlib
from pathlib import Path
import sys
import tempfile
import time
import unittest

from cubrid_language.validation import PROFILE, Validator, WorkerConfig


class ValidatorTests(unittest.TestCase):
    def test_missing_configuration_is_visible_even_for_empty_documents(self):
        with Validator() as validator:
            for text in ('', 'SELECT 1;'):
                with self.subTest(text=text):
                    result = validator.validate(text, PROFILE, 'sql')
                    self.assertEqual((result.status, result.coverage, result.profile),
                                     ('tool-error', 'none', PROFILE))
                    self.assertEqual(result.diagnostics[0].code, 'CUBRID-T1001')

    def test_invalid_inputs_modes_profiles_and_configuration_are_tool_input_failures(self):
        for text, profile, mode, config in (
            (None, PROFILE, 'sql', None),
            (b'SELECT 1;', PROFILE, 'sql', None),
            ('\ud800', PROFILE, 'sql', None),
            ('SELECT 1;\0', PROFILE, 'sql', None),
            ('', PROFILE, 'SQL', None),
            ('', PROFILE, None, None),
            ('', '', 'sql', None),
            ('', None, 'sql', None),
            ('', PROFILE, 'sql', {}),
        ):
            with self.subTest(text=repr(text), profile=profile, mode=mode, config=config):
                with Validator(config) as validator:
                    result = validator.validate(text, profile, mode)
                self.assertEqual(result.status, 'tool-error')
                self.assertEqual(result.diagnostics[0].code, 'CUBRID-T1003')

    def test_explicit_missing_worker_is_never_found_through_the_environment(self):
        config = WorkerConfig(Path('/nonexistent/trusted-parser-worker'), Path('/explicit/runtime'))
        with Validator(config) as validator:
            self.assertEqual(validator.validate('', PROFILE, 'csql').diagnostics[0].code,
                             'CUBRID-T1001')

    def test_closed_validator_fails_explicitly_and_close_is_idempotent(self):
        validator = Validator()
        validator.close()
        validator.close()
        result = validator.validate('', PROFILE, 'sql')
        self.assertEqual(result.status, 'tool-error')
        self.assertEqual(result.diagnostics[0].code, 'CUBRID-T1002')

    def test_close_interrupts_active_and_queued_validation_without_a_late_worker_launch(self):
        from cubrid_language.validation.profiles import qualified_identity

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / 'manifest.json'
            manifest.write_text('{}')
            prefix = root / 'runtime'
            identity = dict(status='ready', manifestDigest=hashlib.sha256(b'{}').hexdigest(),
                            **qualified_identity(PROFILE, prefix))
            executable = root / 'protocol-worker'
            executable.write_text(
                f'#!{sys.executable}\n'
                'import json, pathlib, sys, time\n'
                f'root=pathlib.Path({str(root)!r})\n'
                "with (root/'launches').open('a') as stream: stream.write('start\\n')\n"
                'for line in sys.stdin:\n'
                ' request=json.loads(line)\n'
                " if request['method']=='initialize':\n"
                f'  reply={identity!r}\n'
                "  reply.update(protocolVersion=1,id=request['id'])\n"
                '  print(json.dumps(reply),flush=True)\n'
                ' else:\n'
                "  (root/'parsing').write_text('ready')\n"
                '  time.sleep(30)\n')
            executable.chmod(0o755)
            validator = Validator(WorkerConfig(executable, prefix))
            try:
                with ThreadPoolExecutor(max_workers=12) as executor:
                    active = executor.submit(validator.validate, 'SELECT 1;', PROFILE, 'sql')
                    deadline = time.monotonic() + 3
                    while not (root / 'parsing').exists() and time.monotonic() < deadline:
                        time.sleep(0.01)
                    self.assertTrue((root / 'parsing').exists())
                    queued = [executor.submit(validator.validate, 'SELECT 1;', PROFILE, 'sql')
                              for _ in range(10)]
                    validator.close()
                    results = [future.result(timeout=3) for future in [active, *queued]]
                self.assertEqual([result.status for result in results], ['tool-error'] * 11)
                self.assertEqual(validator.validate('', PROFILE, 'sql').diagnostics[0].code,
                                 'CUBRID-T1002')
                self.assertEqual((root / 'launches').read_text(), 'start\n')
            finally:
                validator.close()


if __name__ == '__main__':
    unittest.main()
