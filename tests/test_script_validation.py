"""Public Validator failures using an explicitly trusted protocol child."""

import hashlib
from pathlib import Path
import sys
import tempfile
import unittest

from cubrid_language.validation import PROFILE, Validator, WorkerConfig
from cubrid_language.validation.profiles import qualified_identity


class ScriptValidationTests(unittest.TestCase):
    def config(self, root, **limits):
        manifest = root / 'manifest.json'
        manifest.write_text('{}')
        prefix = root / 'runtime'
        identity = {'status': 'ready', 'manifestDigest': hashlib.sha256(b'{}').hexdigest(),
                    **qualified_identity(PROFILE, prefix)}
        executable = root / 'worker'
        executable.write_text(f'#!{sys.executable}\n' +
            "import json, sys\n" + f"identity={identity!r}\n" +
            "for line in sys.stdin:\n"
            " request=json.loads(line)\n"
            " if request['method']=='initialize':\n"
            "  result=dict(identity) if request['profile']==identity['profile'] else "
            "{'status':'unsupported','code':'CUBRID-U1001'}\n"
            " elif request['method']=='shutdown':\n"
            "  result={'status':'closed'}\n"
            " else:\n"
            "  text=request['text']\n"
            "  if 'SELECT 9' in text: raise SystemExit(9)\n"
            "  result={'status':'syntax-error','profile':identity['profile'],'coverage':'complete',"
            "'manifestDigest':identity['manifestDigest'],'statementKinds':[], 'syntaxSettingsUnchanged':True,"
            "'diagnostics':[{'code':'CUBRID-S1001','category':'syntax','severity':'error','message':'syntax rejected',"
            "'span':{'start':0,'end':len(text)},'rangePrecision':'statement'}],"
            "'coverageDecisions':[{'start':0,'end':len(text),'admitted':True}],"
            "'nativeObservations':[{'hasTree':False,'treeCount':0,'hasError':True,'hasInternalError':False,"
            "'errorCount':1,'partialStackCount':0,'nativeErrorId':0}]}\n"
            " result.update(protocolVersion=1,id=request['id'])\n"
            " print(json.dumps(result),flush=True)\n"
            " if request['method']=='shutdown': break\n")
        executable.chmod(0o755)
        return WorkerConfig(executable, prefix, **limits)

    def test_later_worker_failure_keeps_prior_syntax_and_later_unsupported_regions(self):
        with tempfile.TemporaryDirectory() as directory:
            with Validator(self.config(Path(directory))) as validator:
                result = validator.validate(';help\nSELECT ;\n;read missing.sql\nSELECT 9;\n;exit\n! touch marker', PROFILE, 'csql')
        self.assertEqual((result.status, result.coverage), ('tool-error', 'partial'))
        self.assertEqual([d.code for d in result.diagnostics],
                         ['CUBRID-S1001', 'CUBRID-U1002', 'CUBRID-T1002', 'CUBRID-U1002'])

    def test_commands_empty_and_unsupported_only_require_profile_and_worker_availability(self):
        with tempfile.TemporaryDirectory() as directory:
            config = self.config(Path(directory))
            for text in ('', ';help\n;exit\n;autocommit on\n;autocommit off', ';read absent.sql'):
                with self.subTest(text=text), Validator(config) as validator:
                    known = validator.validate(text, PROFILE, 'csql')
                    self.assertEqual(known.status, 'unsupported' if text.startswith(';read') else 'valid')
                    unknown = validator.validate(text, 'unknown-profile', 'csql')
                    self.assertEqual((unknown.status, unknown.coverage), ('unsupported', 'none'))
                    self.assertIn('CUBRID-U1001', [d.code for d in unknown.diagnostics])
                missing = WorkerConfig(Path('/nonexistent/script-worker'), Path('/explicit/runtime'))
                with Validator(missing) as validator:
                    unavailable = validator.validate(text, PROFILE, 'csql')
                self.assertEqual((unavailable.status, unavailable.coverage), ('tool-error', 'none'))
                self.assertIn('CUBRID-T1001', [d.code for d in unavailable.diagnostics])

    def test_document_diagnostic_limit_is_not_reset_at_command_boundaries(self):
        with tempfile.TemporaryDirectory() as directory:
            with Validator(self.config(Path(directory), max_diagnostics=3)) as validator:
                result = validator.validate('SELECT ;\n;read a\n;read b\n;read c', PROFILE, 'csql')
        self.assertEqual((result.status, len(result.diagnostics)), ('tool-error', 3))
        self.assertEqual([d.code for d in result.diagnostics], ['CUBRID-S1001', 'CUBRID-U1002', 'CUBRID-T1002'])
        self.assertIn('truncated', result.diagnostics[-1].message)

    def test_rejected_profile_cannot_classify_opaque_content_as_syntax(self):
        with tempfile.TemporaryDirectory() as directory:
            config = self.config(Path(directory))
            with Validator(config) as validator:
                for mode in ('sql', 'csql'):
                    for text in ("BEGIN\n'open", "CREATE PROCEDURE p() AS BEGIN SELECT 'open",
                                 ";read missing.sql\nBEGIN\n'open"):
                        with self.subTest(mode=mode, text=text):
                            result = validator.validate(text, 'unknown-profile', mode)
                            self.assertEqual((result.status, result.coverage), ('unsupported', 'none'))
                            self.assertEqual([d.code for d in result.diagnostics], ['CUBRID-U1001'])
                known = validator.validate("BEGIN\n'open", PROFILE, 'csql')
                self.assertEqual((known.status, known.coverage), ('syntax-error', 'none'))
                self.assertEqual([d.code for d in known.diagnostics], ['CUBRID-S1001', 'CUBRID-U1002'])
            limited = WorkerConfig(config.executable, config.runtime_prefix, max_document_bytes=8)
            with Validator(limited) as validator:
                for text in ('\ud800', '\0', "BEGIN\n'open"):
                    with self.subTest(invalid=repr(text)):
                        result = validator.validate(text, 'unknown-profile', 'csql')
                        self.assertEqual((result.status, result.diagnostics[0].code), ('tool-error', 'CUBRID-T1003'))

    def test_csql_commands_cannot_bypass_input_limits_or_closed_ownership(self):
        missing = WorkerConfig(Path('/nonexistent/script-worker'), Path('/explicit/runtime'), max_document_bytes=8)
        with Validator(missing) as validator:
            for text in (';help\n;exit', ';help\0', ';help\ud800'):
                with self.subTest(text=repr(text)):
                    self.assertEqual(validator.validate(text, PROFILE, 'csql').diagnostics[0].code, 'CUBRID-T1003')
        self.assertEqual(validator.validate(';help', PROFILE, 'csql').diagnostics[0].code, 'CUBRID-T1002')


if __name__ == '__main__':
    unittest.main()
