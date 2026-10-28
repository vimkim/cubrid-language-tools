"""Mandatory native qualification checks: build the explicit runtime first."""

import json
import shutil
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
BUILD = ROOT / "native/parser-worker/build"
PROFILE = "cubrid-11.5.0.2704-cc94778"


class NativeWorkerTests(unittest.TestCase):
    def parse(self, text):
        return self.exchange([
            {"protocolVersion": 1, "id": 1, "method": "initialize", "profile": PROFILE},
            {"protocolVersion": 1, "id": 2, "method": "parse", "text": text},
        ])[1]

    def exchange(self, requests, manifest=None):
        result = subprocess.run(
            [str(BUILD / "parser-worker"), "--manifest", str(manifest or BUILD / "manifest.json")],
            input="".join(json.dumps(request, ensure_ascii=False) + "\n" for request in requests),
            text=True, encoding="utf-8", capture_output=True, timeout=10,
            env={"PATH": "/usr/bin:/bin", "HOME": "/nonexistent", "LANG": "C.UTF-8"},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return [json.loads(line) for line in result.stdout.splitlines()]

    def test_initialize_identifies_exact_qualified_runtime(self):
        result, = self.exchange([{"protocolVersion": 1, "id": 1, "method": "initialize", "profile": PROFILE}])
        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["profile"], PROFILE)
        self.assertEqual(result["nativeVersion"], "11.5.0.2704-cc94778")
        self.assertEqual(result["sourceCommit"], "cc947788d3b7dc402f46192d0f3299ddcc8563ba")
        self.assertEqual(result["supportedStatementKinds"], ["PT_SELECT", "PT_CREATE_SERIAL"])

    def test_create_serial_is_checked_by_the_native_parser(self):
        valid = self.parse("CREATE SERIAL order_no START WITH 10 INCREMENT BY 2;")
        self.assertEqual(valid["status"], "valid")
        self.assertEqual(valid["statementKinds"], ["PT_CREATE_SERIAL"])
        invalid = self.parse("CREATE SERIAL order_no START WITH ;")
        self.assertEqual(invalid["status"], "syntax-error")
        self.assertEqual(invalid["diagnostics"][0]["code"], "CUBRID-S1001")
        korean = self.parse("-- 한글 😀\r\nCREATE SERIAL 주문 START WITH ;")
        self.assertEqual(korean["status"], "syntax-error")
        self.assertTrue(korean["coverageDecisions"][0]["admitted"])

    def test_unaudited_query_forms_never_enter_native_parser(self):
        for text in ("SELECT * FROM missing_table;", "WITH x AS (SELECT 1) SELECT 1;",
                     "SELECT (SELECT 1);", "SELECT sleep(1);", "SELECT 1+2;",
                     "SELECT /*+ RECOMPILE */ 1;", "DROP TABLE never_execute;"):
            with self.subTest(text=text):
                result = self.parse(text)
                self.assertEqual(result["status"], "unsupported")
                self.assertEqual(result["nativeObservations"], [])

    def test_empty_multiple_incomplete_and_literal_inputs(self):
        for text, status, kinds in (
            ("", "valid", []), ("-- 한글 😀\r\n", "valid", []),
            ("SELECT '한글 😀', -10, NULL;", "valid", ["PT_SELECT"]),
            ("SELECT 1; CREATE SERIAL s START WITH 10;", "valid", ["PT_SELECT", "PT_CREATE_SERIAL"]),
            ("SELECT", "syntax-error", []), ("SELECT 1,", "syntax-error", []),
            ("SELECT 'unfinished", "syntax-error", []),
            ("SELECT 1,; DROP TABLE never_execute;", "syntax-error", []),
        ):
            with self.subTest(text=text):
                result = self.parse(text)
                self.assertEqual(result["status"], status)
                self.assertEqual(result["statementKinds"], kinds)

    def test_unicode_errors_expose_only_statement_precision(self):
        for text in ("SELECT '가', ;", "SELECT '😀', ;", "-- 가😀\r\nSELECT '가😀', ;"):
            with self.subTest(text=text):
                result = self.parse(text)
                self.assertEqual(result["status"], "syntax-error")
                self.assertEqual(result["diagnostics"][0]["span"], {"start": 0, "end": len(text)})
                self.assertEqual(result["diagnostics"][0]["rangePrecision"], "statement")

    def test_unknown_profile_never_initializes(self):
        result, = self.exchange([{"protocolVersion": 1, "id": 1, "method": "initialize", "profile": "cubrid-11.4"}])
        self.assertEqual((result["status"], result["code"]), ("unsupported", "CUBRID-U1001"))

    def test_manifest_tampering_and_missing_manifest_are_distinct(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            request = {"protocolVersion": 1, "id": 1, "method": "initialize", "profile": PROFILE}
            missing, = self.exchange([request], path)
            self.assertEqual(missing["code"], "CUBRID-T1001")
            path.write_text((BUILD / "manifest.json").read_text() + " ")
            mismatch, = self.exchange([request], path)
            self.assertEqual(mismatch["code"], "CUBRID-T1002")

    def test_runtime_prefix_mismatch_is_rejected_before_parsing(self):
        result, = self.exchange([{"protocolVersion": 1, "id": 1, "method": "initialize", "profile": PROFILE,
                                  "runtimePrefix": "/wrong/runtime"}])
        self.assertEqual(result["code"], "CUBRID-T1003")

    def test_invalid_requests_nul_and_limit_cannot_become_a_pass(self):
        result, = self.exchange([{"protocolVersion": 99, "id": 1, "method": "initialize"}])
        self.assertEqual(result["status"], "tool-error")
        self.assertEqual(self.parse("SELECT '\0';")["code"], "CUBRID-T1003")
        self.assertEqual(self.parse(" " * (8 * 1024 * 1024 + 1))["code"], "CUBRID-T1003")
        limited = self.parse("SELECT ,;" * 257)
        self.assertEqual(limited["status"], "tool-error")
        self.assertIn("truncated", limited["message"])

    def test_partial_tree_and_ordinary_errors_do_not_become_success(self):
        result = self.parse("CREATE SERIAL s START WITH 1 START WITH 2;")
        self.assertEqual(result["status"], "syntax-error")
        self.assertGreater(result["nativeObservations"][0]["partialStackCount"], 0)
        self.assertTrue(result["nativeObservations"][0]["hasError"])
        self.assertFalse(result["nativeObservations"][0]["hasInternalError"])

    def test_internal_error_is_induced_only_in_a_separate_test_build(self):
        manifest = json.loads((BUILD / "manifest.json").read_text())
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "test-build"
            result = subprocess.run(["python3", str(ROOT / "native/parser-worker/build.py"),
                "--source", manifest["source"], "--generated", str(Path(manifest["library"]).parents[1]),
                "--library", manifest["library"], "--runtime-prefix", manifest["runtimePrefix"],
                "--output", str(output), "--test-internal-error"], capture_output=True, text=True, timeout=60)
            self.assertEqual(result.returncode, 0, result.stderr)
            process = subprocess.run([str(output / "parser-worker"), "--manifest", str(output / "manifest.json")],
                input="".join(json.dumps(r) + "\n" for r in (
                    {"protocolVersion": 1, "id": 1, "method": "initialize", "profile": PROFILE},
                    {"protocolVersion": 1, "id": 2, "method": "parse", "text": "SELECT 1;"})),
                text=True, capture_output=True, timeout=10)
            self.assertEqual(process.returncode, 0, process.stderr)
            identity, result = [json.loads(line) for line in process.stdout.splitlines()]
            self.assertTrue(identity["testOnly"])
            self.assertEqual(result["status"], "tool-error")
            self.assertEqual(result["diagnostics"][0]["code"], "CUBRID-T1002")
            self.assertTrue(result["nativeObservations"][0]["hasTree"])
            self.assertTrue(result["nativeObservations"][0]["hasInternalError"])
            self.assertEqual(result["statementKinds"], [])
        identity, result = self.exchange([
            {"protocolVersion": 1, "id": 1, "method": "initialize", "profile": PROFILE},
            {"protocolVersion": 1, "id": 2, "method": "parse", "text": "SELECT 1;", "testInternalError": True}])
        self.assertFalse(identity["testOnly"])
        self.assertEqual(result["status"], "valid")

    def test_missing_or_modified_runtime_assets_fail_before_parsing(self):
        manifest = json.loads((BUILD / "manifest.json").read_text())
        with tempfile.TemporaryDirectory() as directory:
            prefix, output = Path(directory) / "runtime", Path(directory) / "build"
            shutil.copytree(Path(manifest["runtimePrefix"]) / "msg", prefix / "msg")
            (prefix / "lib").mkdir()
            shutil.copy2(Path(manifest["runtimePrefix"]) / "lib/libcubrid_timezones.so.11.5", prefix / "lib")
            result = subprocess.run(["python3", str(ROOT / "native/parser-worker/build.py"),
                "--source", manifest["source"], "--generated", str(Path(manifest["library"]).parents[1]),
                "--library", manifest["library"], "--runtime-prefix", str(prefix), "--output", str(output)],
                capture_output=True, text=True, timeout=60)
            self.assertEqual(result.returncode, 0, result.stderr)
            asset = next((prefix / "msg/en_US.utf8").glob("*.cat"))
            asset.unlink()
            request = json.dumps({"protocolVersion": 1, "id": 1, "method": "initialize", "profile": PROFILE}) + "\n"
            for expected in ("CUBRID-T1001", "CUBRID-T1002"):
                result = subprocess.run([str(output / "parser-worker"), "--manifest", str(output / "manifest.json")],
                    input=request, text=True, capture_output=True, timeout=10)
                self.assertEqual(json.loads(result.stdout)["code"], expected)
                asset.write_bytes(b"not the qualified message catalog")

    def test_invalid_wire_encoding_is_an_input_failure(self):
        for text in (b'"\xff"', b'"\\ud800"'):
            request = b'{"protocolVersion":1,"id":1,"method":"parse","text":' + text + b'}\n'
            result = subprocess.run([str(BUILD / "parser-worker"), "--manifest", str(BUILD / "manifest.json")],
                                    input=request, capture_output=True, timeout=10)
            self.assertEqual(json.loads(result.stdout)["code"], "CUBRID-T1003")

    def test_build_rejects_a_different_library_without_touching_shared_inputs(self):
        manifest = json.loads((BUILD / "manifest.json").read_text())
        with tempfile.TemporaryDirectory() as directory:
            wrong = Path(directory) / "libwrong.so"
            wrong.write_bytes(b"not the qualified binary")
            result = subprocess.run(["python3", str(ROOT / "native/parser-worker/build.py"),
                "--source", manifest["source"], "--generated", str(Path(manifest["library"]).parents[1]),
                "--library", str(wrong), "--runtime-prefix", manifest["runtimePrefix"]], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("library SHA-256 differs", result.stderr)


if __name__ == "__main__":
    unittest.main()
