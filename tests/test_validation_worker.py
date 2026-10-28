import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading
import hashlib
import json
from pathlib import Path
import tempfile
import time
import unittest

from cubrid_language.validation import NativeWorker, WorkerConfig
from cubrid_language.models import Span
from cubrid_language.validation.profiles import qualified_identity

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "native/parser-worker/build"
PREFIX = Path("/unused/explicit-runtime")


class WorkerAdapterTests(unittest.TestCase):
    def test_truncated_tail_must_cover_the_contiguous_unprocessed_original_source(self):
        text = 'SELECT ,; CREATE PROCEDURE p;'
        syntax = {"code": "CUBRID-S1001", "category": "syntax", "severity": "error",
                  "message": "rejected", "span": {"start": 0, "end": 9}, "rangePrecision": "statement"}
        for tail_start, marker_start in ((9, 9), (10, 10), (9, 0), (9, 1)):
            with self.subTest(tail_start=tail_start, marker_start=marker_start), tempfile.TemporaryDirectory() as directory:
                marker = {**syntax, "code": "CUBRID-T1002", "category": "tool", "message": "result truncated",
                          "span": {"start": marker_start, "end": len(text)}}
                response = {"status": "tool-error", "coverage": "partial", "diagnosticsTruncated": True,
                    "diagnostics": [{**syntax, "message": str(index)} for index in range(255)] + [marker],
                    "statementKinds": [], "coverageDecisions": [{"start": 0, "end": 9, "admitted": True},
                        {"start": tail_start, "end": len(text), "admitted": False}],
                    "nativeObservations": [{"hasTree": False, "treeCount": 0, "hasError": True,
                        "hasInternalError": False, "errorCount": 255, "nativeErrorId": 0, "partialStackCount": 0}]}
                executable = self.reply_worker(directory, response)
                with NativeWorker(WorkerConfig(executable, PREFIX)) as worker:
                    result = worker.parse(text)
                accepted = (tail_start, marker_start) in ((9, 9), (9, 0))
                self.assertEqual(result.coverage, 'partial' if accepted else 'none')
                self.assertEqual(len(result.diagnostics), 256 if accepted else 1)
        with tempfile.TemporaryDirectory() as directory:
            marker = {**syntax, "code": "CUBRID-T1002", "category": "tool", "message": "result truncated",
                      "span": {"start": 9, "end": len(text)}}
            response = {"status": "tool-error", "coverage": "partial", "diagnosticsTruncated": True,
                "diagnostics": [{**syntax, "message": str(index), "span": {"start": 9, "end": len(text)}}
                                for index in range(255)] + [marker], "statementKinds": [],
                "coverageDecisions": [{"start": 0, "end": 9, "admitted": False},
                                      {"start": 9, "end": len(text), "admitted": True}],
                "nativeObservations": [{"hasTree": False, "treeCount": 0, "hasError": True,
                    "hasInternalError": False, "errorCount": 300, "nativeErrorId": 0, "partialStackCount": 0}]}
            executable = self.reply_worker(directory, response)
            with NativeWorker(WorkerConfig(executable, PREFIX)) as worker:
                result = worker.parse(text)
            self.assertEqual((result.status, result.coverage, len(result.diagnostics)), ('tool-error', 'none', 1))

    def test_native_truncation_marker_requires_consistent_bounded_unsuccessful_result(self):
        syntax = {"code": "CUBRID-S1001", "category": "syntax", "severity": "error",
                  "message": "rejected", "span": {"start": 0, "end": 9}, "rangePrecision": "statement"}
        marker = {**syntax, "code": "CUBRID-T1002", "category": "tool", "message": "result truncated"}
        diagnostics = [{**syntax, "message": str(index)} for index in range(255)] + [marker]
        base = {"status": "tool-error", "coverage": "partial", "diagnosticsTruncated": True,
                "diagnostics": diagnostics, "statementKinds": [], "nativeObservations": [{
                    "hasTree": False, "treeCount": 0, "hasError": True, "hasInternalError": False,
                    "errorCount": 300, "nativeErrorId": 0, "partialStackCount": 0}]}
        for changes in ({}, {"diagnosticsTruncated": 1}, {"diagnosticsTruncated": "true"},
                        {"diagnosticsTruncated": None}, {"diagnosticsTruncated": False},
                        {"coverage": "complete"}, {"status": "valid"},
                        {"diagnostics": []}, {"diagnostics": diagnostics[:-1]}, {"diagnostics": diagnostics + [marker]},
                        {"diagnostics": diagnostics[:-1] + [{**marker, "span": {"start": 0, "end": 8}}]}):
            with self.subTest(changes=list(changes)), tempfile.TemporaryDirectory() as directory:
                executable = self.reply_worker(directory, {**base, **changes})
                with NativeWorker(WorkerConfig(executable, PREFIX)) as worker:
                    result = worker.parse('SELECT ,;')
                self.assertEqual(result.status, 'tool-error')
                self.assertEqual(result.coverage, 'partial' if not changes else 'none')
                self.assertEqual(len(result.diagnostics), 256 if not changes else 1)

    def test_unreported_native_error_cannot_be_returned_as_a_pass(self):
        for native_error in (-224, True, "0", None):
            with self.subTest(native_error=native_error), tempfile.TemporaryDirectory() as directory:
                observation = {"hasTree": True, "treeCount": 1, "hasInternalError": False,
                               "hasError": False, "errorCount": 0, "partialStackCount": 0,
                               "nativeErrorId": native_error}
                executable = self.reply_worker(directory, {"nativeObservations": [observation]})
                with NativeWorker(WorkerConfig(executable, PREFIX)) as worker:
                    result = worker.parse("SELECT 1;")
                self.assertEqual(result.status, "tool-error")
                self.assertEqual(result.diagnostics[0].code, "CUBRID-T1002")

    def test_validation_uses_the_shared_span_value(self):
        from cubrid_language.validation import Span as ValidationSpan
        self.assertIs(ValidationSpan, Span)

    def test_unavailable_and_bad_input_have_distinct_codes(self):
        with NativeWorker(WorkerConfig(Path("/nonexistent/parser-worker"), PREFIX)) as worker:
            self.assertEqual(worker.parse("").diagnostics[0].code, "CUBRID-T1001")
            self.assertEqual(worker.parse("SELECT '\0';").diagnostics[0].code, "CUBRID-T1003")
            self.assertEqual(worker.parse("\ud800").diagnostics[0].code, "CUBRID-T1003")

    def fake(self, directory, body):
        executable = Path(directory) / "worker"
        executable.write_text("#!/usr/bin/python3\n" + body)
        executable.chmod(0o755)
        return executable

    def reply_worker(self, directory, response, identity_changes=None, *, omit=()):
        manifest = Path(directory) / "manifest.json"
        manifest.write_text("{}")
        digest = hashlib.sha256(manifest.read_bytes()).hexdigest()
        identity = {"status": "ready", "manifestDigest": digest,
                    **qualified_identity("cubrid-11.5.0.2704-cc94778", PREFIX), **(identity_changes or {})}
        result = {"status": "valid", "profile": identity["profile"], "coverage": "complete",
                  "diagnostics": [], "statementKinds": ["PT_SELECT"], "manifestDigest": digest,
                  "syntaxSettingsUnchanged": True,
                  "coverageDecisions": [{"start": 0, "end": 9, "admitted": True}],
                  "nativeObservations": [{"hasTree": True, "treeCount": 1, "hasInternalError": False,
                                          "hasError": False, "errorCount": 0, "nativeErrorId": 0, "partialStackCount": 0}], **response}
        for key in omit:
            result.pop(key)
        return self.fake(directory, "import json,sys\n"
            f"identity={identity!r}\nresult={result!r}\n"
            "for line in sys.stdin:\n"
            " request=json.loads(line)\n"
            " value=dict(identity if request['method']=='initialize' else result)\n"
            " value.update(protocolVersion=1,id=request['id'])\n"
            " print(json.dumps(value),flush=True)\n")

    def test_diagnostic_code_category_and_severity_must_agree(self):
        for changes in ({"code": "CUBRID-U1002"}, {"severity": "warning"}, {"code": "unknown"}):
            with self.subTest(changes=changes), tempfile.TemporaryDirectory() as directory:
                diagnostic = {"code": "CUBRID-S1001", "category": "syntax", "severity": "error",
                              "message": "rejected", "span": {"start": 0, "end": 9},
                              "rangePrecision": "statement", **changes}
                executable = self.reply_worker(directory, {"status": "syntax-error", "diagnostics": [diagnostic]})
                with NativeWorker(WorkerConfig(executable, PREFIX)) as worker:
                    result = worker.parse("SELECT 1;")
                self.assertEqual(result.status, "tool-error")
                self.assertEqual(result.diagnostics[0].code, "CUBRID-T1002")

    def test_initialize_and_parse_must_match_the_configured_manifest(self):
        for response, identity_changes in (({}, {"manifestDigest": "a" * 64}),
                                           ({"manifestDigest": "b" * 64}, {}),
                                           ({"manifestDigest": None}, {})):
            with self.subTest(response=response, identity=identity_changes), tempfile.TemporaryDirectory() as directory:
                executable = self.reply_worker(directory, response, identity_changes)
                with NativeWorker(WorkerConfig(executable, PREFIX)) as worker:
                    result = worker.parse("SELECT 1;")
                self.assertEqual(result.status, "tool-error")
                self.assertEqual(result.diagnostics[0].code, "CUBRID-T1002")

    def test_prior_coverage_revision_and_unqualified_kinds_are_rejected(self):
        for response, identity, expected in (({}, {"coverageRevision": "literal-select-create-serial-v1"}, "unsupported"),
                                             ({}, {"coverageRevision": "bounded-query-dml-create-serial-v2"}, "unsupported"),
                                             ({}, {"supportedStatementKinds": ["PT_SELECT", "PT_CREATE_SERIAL"]}, "unsupported"),
                                             ({"statementKinds": ["PT_CREATE_USER"]}, {}, "tool-error")):
            with self.subTest(response=response, identity=identity), tempfile.TemporaryDirectory() as directory:
                executable = self.reply_worker(directory, response, identity)
                with NativeWorker(WorkerConfig(executable, PREFIX)) as worker:
                    result = worker.parse("SELECT 1;")
                self.assertEqual(result.status, expected)
                self.assertEqual(result.diagnostics[0].code, "CUBRID-U1001" if expected == "unsupported" else "CUBRID-T1002")

    def test_ranges_coverage_status_and_native_observations_must_be_consistent(self):
        unsupported = {"code": "CUBRID-U1002", "category": "unsupported", "severity": "warning",
                       "message": "outside coverage", "span": {"start": 0, "end": 9}, "rangePrecision": "statement"}
        for response in (
            {"syntaxSettingsUnchanged": False},
            {"syntaxSettingsUnchanged": 1},
            {"syntaxSettingsUnchanged": "true"},
            {"syntaxSettingsUnchanged": None},
            {"status": "unsupported", "diagnostics": [unsupported]},
            {"coverage": "partial"},
            {"coverageDecisions": [{"start": 0, "end": 10, "admitted": True}]},
            {"coverageDecisions": [{"start": True, "end": 9, "admitted": True}]},
            {"coverageDecisions": [{"start": 0, "end": 9, "admitted": False}]},
            {"nativeObservations": []},
            {"nativeObservations": [{"hasTree": True, "treeCount": 1, "hasInternalError": True,
                                     "hasError": False, "errorCount": 0, "nativeErrorId": 0, "partialStackCount": 0}]},
            {"statementKinds": [], "nativeObservations": [{"hasTree": False, "treeCount": 0,
                "hasInternalError": False, "hasError": False, "errorCount": 0, "nativeErrorId": 0, "partialStackCount": 0}]},
            {"statementKinds": [], "nativeObservations": [{"hasTree": True, "treeCount": 2,
                "hasInternalError": False, "hasError": False, "errorCount": 0, "nativeErrorId": 0, "partialStackCount": 0}]},
            {"nativeObservations": [{"hasTree": False, "treeCount": 1,
                "hasInternalError": False, "hasError": False, "errorCount": 0, "nativeErrorId": 0, "partialStackCount": 0}]},
            {"coverageDecisions": [], "nativeObservations": [], "statementKinds": []},
            {"coverageDecisions": [{"start": 1, "end": 9, "admitted": True}]},
            {"statementKinds": []},
            {"diagnostics": [{**unsupported, "span": {"start": 0, "end": 10}}], "status": "unsupported"},
        ):
            with self.subTest(response=response), tempfile.TemporaryDirectory() as directory:
                executable = self.reply_worker(directory, response)
                with NativeWorker(WorkerConfig(executable, PREFIX)) as worker:
                    result = worker.parse("SELECT 1;")
                self.assertEqual(result.status, "tool-error")
                self.assertEqual(result.diagnostics[0].code, "CUBRID-T1002")

        with self.subTest(response="missing settings marker"), tempfile.TemporaryDirectory() as directory:
            executable = self.reply_worker(directory, {}, omit=("syntaxSettingsUnchanged",))
            with NativeWorker(WorkerConfig(executable, PREFIX)) as worker:
                result = worker.parse("SELECT 1;")
            self.assertEqual(result.status, "tool-error")
            self.assertEqual(result.diagnostics[0].code, "CUBRID-T1002")
        with self.subTest(response="bare native failure"), tempfile.TemporaryDirectory() as directory:
            executable = self.reply_worker(directory, {"status": "tool-error", "code": "CUBRID-T1003",
                "message": "native input rejected"}, omit=("diagnostics", "syntaxSettingsUnchanged"))
            with NativeWorker(WorkerConfig(executable, PREFIX)) as worker:
                result = worker.parse("SELECT 1;")
            self.assertEqual(result.status, "tool-error")
            self.assertEqual(result.diagnostics[0].code, "CUBRID-T1003")

    def test_unrecognized_failure_codes_and_noninteger_protocol_versions_are_rejected(self):
        for response, identity in (({"status": "tool-error", "diagnostics": None, "code": "other"}, {}),
                                   ({}, {"status": "tool-error", "code": "other", "message": "bad"}),
                                   ({}, {"testOnly": 0})):
            with self.subTest(response=response, identity=identity), tempfile.TemporaryDirectory() as directory:
                executable = self.reply_worker(directory, response, identity)
                with NativeWorker(WorkerConfig(executable, PREFIX)) as worker:
                    result = worker.parse("SELECT 1;")
                self.assertEqual(result.status, "tool-error")
                self.assertEqual(result.diagnostics[0].code, "CUBRID-T1002")
        with tempfile.TemporaryDirectory() as directory:
            executable = self.fake(directory, "import json\nprint(json.dumps({'protocolVersion':True,'id':1,'status':'unsupported'}),flush=True)\n")
            with NativeWorker(WorkerConfig(executable, PREFIX)) as worker:
                self.assertEqual(worker.parse("").diagnostics[0].code, "CUBRID-T1002")

    def test_unterminated_output_cannot_defeat_deadline_or_response_limit(self):
        for body, limit in (("import time\nprint('{', end='', flush=True)\ntime.sleep(10)\n", 1024),
                            ("import os\nos.write(1, b'x' * 8192)\n", 1024),
                            ("import os,time\nif os.fork() == 0:\n time.sleep(1)\nelse:\n os._exit(0)\n", 1024)):
            with self.subTest(body=body), tempfile.TemporaryDirectory() as directory:
                config = WorkerConfig(self.fake(directory, body), PREFIX, timeout=0.15, max_response_bytes=limit)
                start = time.monotonic()
                with NativeWorker(config) as worker:
                    result = worker.parse("SELECT 1;")
                    self.assertEqual(result.status, "tool-error")
                    self.assertEqual(result.diagnostics[0].code, "CUBRID-T1002")
                self.assertLess(time.monotonic() - start, 0.8)

    def test_crash_bad_json_and_wrong_response_id_are_tool_failures(self):
        for body in ("raise SystemExit(9)\n", "print('bad json', flush=True)\n",
                     "import json\nprint(json.dumps({'protocolVersion':1,'id':99,'status':'ready'}), flush=True)\n"):
            with self.subTest(body=body), tempfile.TemporaryDirectory() as directory:
                with NativeWorker(WorkerConfig(self.fake(directory, body), PREFIX)) as worker:
                    self.assertEqual(worker.parse("SELECT 1;").diagnostics[0].code, "CUBRID-T1002")

    def test_async_parse_does_not_block_event_loop_and_cancellation_reaps_owned_worker(self):
        async def scenario(executable):
            worker = NativeWorker(WorkerConfig(executable, PREFIX))
            task = asyncio.create_task(worker.parse_async("SELECT 1;"))
            await asyncio.sleep(0.05)
            self.assertFalse(task.done())
            process = worker.process
            self.assertIsNotNone(process)
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await task
            self.assertIsNotNone(process.poll())
            worker.close()
        with tempfile.TemporaryDirectory() as directory:
            executable = self.fake(directory, "import time\ntime.sleep(10)\n")
            asyncio.run(scenario(executable))

    def test_cancellation_before_executor_start_cannot_launch_a_worker_later(self):
        async def scenario(executable):
            gate = threading.Event()
            loop = asyncio.get_running_loop()
            loop.set_default_executor(ThreadPoolExecutor(max_workers=1))
            blocker = loop.run_in_executor(None, gate.wait)
            timer = threading.Timer(0.3, gate.set)
            timer.start()
            worker = NativeWorker(WorkerConfig(executable, PREFIX))
            try:
                task = asyncio.create_task(worker.parse_async("SELECT 1;"))
                await asyncio.sleep(0.02)
                start = time.monotonic()
                task.cancel()
                with self.assertRaises(asyncio.CancelledError):
                    await task
                self.assertLess(time.monotonic() - start, 0.15)
                await blocker
                await asyncio.sleep(0.02)
                self.assertIsNone(worker.process)
            finally:
                gate.set()
                timer.join()
                worker.close()
        with tempfile.TemporaryDirectory() as directory:
            executable = self.fake(directory, "raise SystemExit(9)\n")
            asyncio.run(scenario(executable))

    def test_unresponsive_idle_shutdown_is_bounded_and_reaps_its_worker(self):
        with tempfile.TemporaryDirectory() as directory:
            executable = self.reply_worker(directory, {})
            executable.write_text(executable.read_text().replace("import json,sys", "import json,sys,time").replace(
                " value=dict", " if request['method']=='shutdown': time.sleep(10)\n value=dict"))
            worker = NativeWorker(WorkerConfig(executable, PREFIX))
            try:
                self.assertEqual(worker.parse("SELECT 1;").status, "valid")
                process = worker.process
                start = time.monotonic()
                worker.close()
                self.assertLess(time.monotonic() - start, 0.8)
                self.assertIsNotNone(process.poll())
            finally:
                worker.close()

    def test_configuration_limits_are_positive_and_bounded(self):
        for changes in ({"timeout": 0}, {"timeout": float("nan")}, {"max_response_bytes": 0},
                        {"max_document_bytes": 100 * 1024 * 1024}, {"max_diagnostics": 257}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                WorkerConfig(BUILD / "parser-worker", PREFIX, **changes)
