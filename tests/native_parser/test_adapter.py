import asyncio
from pathlib import Path
import json
import unittest

from cubrid_language.validation import NativeWorker, WorkerConfig

BUILD = Path(__file__).resolve().parents[2] / "native/parser-worker/build"


class NativeAdapterTests(unittest.TestCase):
    def test_retained_query_dml_corpus_preserves_status_kinds_and_original_spans(self):
        corpus = json.loads((BUILD.parent / "qualification/corpus.json").read_text())
        with NativeWorker(self.config()) as worker:
            for case in corpus["cases"]:
                with self.subTest(case=case["id"]):
                    result = worker.parse(case["text"])
                    self.assertEqual(result.status, case["expected"], result)
                    self.assertEqual(list(result.statement_kinds), case["kinds"])
                    for diagnostic in result.diagnostics:
                        self.assertEqual(diagnostic.range_precision, "statement")
                        self.assertGreaterEqual(diagnostic.span.start, 0)
                        self.assertLessEqual(diagnostic.span.end, len(case["text"]))
                        if len(case["admitted"]) == 1:
                            self.assertEqual((diagnostic.span.start, diagnostic.span.end), (0, len(case["text"])))

    def config(self):
        manifest = json.loads((BUILD / "manifest.json").read_text())
        return WorkerConfig(BUILD / "parser-worker", Path(manifest["runtimePrefix"]))

    def test_native_results_are_immutable_and_profile_mismatch_is_unsupported(self):
        with NativeWorker(self.config()) as worker:
            self.assertEqual(worker.parse("SELECT 1;").status, "valid")
            error = worker.parse("CREATE SERIAL s START WITH ;")
            self.assertEqual(error.status, "syntax-error")
            self.assertEqual(error.diagnostics[0].code, "CUBRID-S1001")
            with self.assertRaises(AttributeError):
                error.status = "valid"
        with NativeWorker(self.config(), profile="wrong") as worker:
            self.assertEqual(worker.parse("").status, "unsupported")

    def test_idle_close_shuts_down_and_removes_only_its_private_runtime(self):
        worker = NativeWorker(self.config())
        try:
            self.assertEqual(worker.parse("SELECT 1;").status, "valid")
            process = worker.process
            scratch = Path(f"/proc/{process.pid}/cwd").readlink()
            self.assertTrue(scratch.name.startswith("cubrid-parser-worker-"))
            self.assertTrue(scratch.is_dir())
            worker.close()
            self.assertEqual(process.returncode, 0)
            self.assertFalse(scratch.exists())
        finally:
            worker.close()

    def test_concurrent_async_requests_are_serialized(self):
        async def scenario():
            with NativeWorker(self.config()) as worker:
                results = await asyncio.gather(worker.parse_async("SELECT 1;"),
                    worker.parse_async("CREATE SERIAL s START WITH ;"), worker.parse_async("SELECT '가😀';"))
                self.assertEqual([result.status for result in results], ["valid", "syntax-error", "valid"])
        asyncio.run(scenario())
