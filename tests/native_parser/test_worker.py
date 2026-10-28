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
    def test_retained_query_dml_qualification_corpus(self):
        corpus = json.loads((ROOT / "native/parser-worker/qualification/corpus.json").read_text())
        requests = [{"protocolVersion": 1, "id": 1, "method": "initialize", "profile": PROFILE}]
        requests += [{"protocolVersion": 1, "id": i + 2, "method": "parse", "text": case["text"]}
                     for i, case in enumerate(corpus["cases"])]
        requests.append({"protocolVersion": 1, "id": len(requests) + 1, "method": "shutdown"})
        responses = self.exchange(requests)
        self.assertEqual(responses[0]["coverageRevision"], corpus["coverageRevision"])
        self.assertEqual(len(responses), len(requests))
        for case, result in zip(corpus["cases"], responses[1:]):
            with self.subTest(case=case["id"]):
                self.assertEqual(result["status"], case["expected"], result)
                self.assertEqual(result["statementKinds"], case["kinds"])
                self.assertEqual([d["admitted"] for d in result["coverageDecisions"]], case["admitted"])
                self.assertEqual(len(result["nativeObservations"]), sum(case["admitted"]))

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
        self.assertEqual(result["coverageRevision"], "bounded-query-dml-create-serial-v2")
        self.assertEqual(result["supportedStatementKinds"], ["PT_SELECT", "PT_INSERT", "PT_UPDATE", "PT_DELETE", "PT_MERGE", "PT_CREATE_SERIAL"])

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

    def test_bounded_queries_use_native_syntax_without_a_catalog(self):
        for text in (
            "SELECT a.id + 2 * (a.id - 1), '가😀' AS label FROM absent_a a LEFT JOIN absent_b b ON a.id = b.id WHERE NOT (a.id < 1 OR b.id IS NULL);",
            "WITH x AS (SELECT 1 AS id) SELECT x.id FROM x;",
            "SELECT (SELECT 1), q.id FROM (SELECT id FROM absent) q WHERE EXISTS (SELECT 1 FROM other_absent);",
        ):
            with self.subTest(text=text):
                result = self.parse(text)
                self.assertEqual(result["status"], "valid", result)
                self.assertEqual(result["statementKinds"], ["PT_SELECT"])
                self.assertEqual(len(result["nativeObservations"]), 1)

    def test_basic_dml_builds_only_parser_trees(self):
        for text, kind in (
            ("INSERT INTO absent (id, label) VALUES (1, '가😀'), (2, NULL);", "PT_INSERT"),
            ("INSERT INTO absent (id) SELECT id FROM other_absent WHERE id > 0;", "PT_INSERT"),
            ("UPDATE absent SET id = id + 1, label = '가😀' WHERE id = 1;", "PT_UPDATE"),
            ("DELETE FROM absent WHERE id = (SELECT 1);", "PT_DELETE"),
            ("MERGE INTO absent a USING other_absent b ON a.id = b.id WHEN MATCHED THEN UPDATE SET a.id = b.id WHEN NOT MATCHED THEN INSERT (id) VALUES (b.id);", "PT_MERGE"),
        ):
            with self.subTest(text=text):
                result = self.parse(text)
                self.assertEqual(result["status"], "valid", result)
                self.assertEqual(result["statementKinds"], [kind])

    def test_feature_closure_blocks_native_calls_even_behind_comments_and_quotes(self):
        for text in (
            "SELECT a. /* hidden */ next_value FROM absent a;",
            'SELECT a."nextval" FROM absent a;', "SELECT a.[currval] FROM absent a;",
            "SELECT a.`current_value` FROM absent a;", "SELECT missing /* hidden */ (1);",
            'SELECT "sleep"(1);', "SELECT [sleep] (1);", "SELECT 1e2;", "SELECT .5;",
            "SELECT 1.;", "SELECT 0xFF;", "SELECT N'한글';", "SELECT _utf8'한글';",
            "SELECT a->b FROM absent;", "SELECT 1 << 2;", "SELECT 1 || 2;",
            "SELECT 1 <=> 1;", "SELECT 1 & 2;", "SELECT @x;", "SELECT ?;",
            "SELECT :x;", "SELECT a FROM absent@remote;", "SELECT 1 INTO x;",
            "WITH x(id) AS (SELECT 1) SELECT id FROM x;", "SELECT a FROM absent a(id);",
            "SELECT * FROM DBLINK('secret', 'select 1') t;", "SELECT 1 UNION SELECT 2;",
            "SELECT /*+ RECOMPILE */ 1;", "SELECT --+ RECOMPILE\n1;", "SELECT //+ RECOMPILE\n1;",
            "SELECT /* outer /* inner */ 1;", "SELECT /*! executable */ 1;",
            "INSERT INTO absent VALUES (sleep(1));", "UPDATE absent SET id = sleep(1);",
            "DELETE FROM absent WHERE id = sleep(1);",
            "MERGE INTO a USING b ON a.id=b.id WHEN MATCHED THEN UPDATE SET a.id=sleep(1);",
        ):
            with self.subTest(text=text):
                result = self.parse(text)
                self.assertEqual(result["status"], "unsupported", result)
                self.assertEqual(result["nativeObservations"], [])

    def test_join_and_assignment_keywords_cannot_enable_reserved_functions(self):
        for text in ("SELECT LEFT('abc',1);", "SELECT RIGHT('abc',1);",
                     "UPDATE absent SET id=SET(SELECT 1);",
                     "MERGE INTO a USING b ON a.id=b.id WHEN MATCHED THEN UPDATE SET a.id=LEFT('a',1);",
                     "MERGE INTO a USING b ON a.id=b.id WHEN MATCHED THEN UPDATE SET a.id=MATCHED(1);"):
            with self.subTest(text=text):
                result = self.parse(text)
                self.assertEqual(result["status"], "unsupported", result)
                self.assertEqual(result["nativeObservations"], [])

    def test_unaudited_query_forms_never_enter_native_parser(self):
        for text in ("SELECT sleep(1);", "WITH RECURSIVE x AS (SELECT 1) SELECT 1;",
                     "SELECT CURRENT_DATE;", "SELECT a.next_value FROM absent a;",
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
