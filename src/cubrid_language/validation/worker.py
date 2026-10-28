"""One owned native process, one outstanding request, bounded nonblocking pipes."""

import asyncio
import copy
from contextlib import suppress
from dataclasses import dataclass
import json
import hashlib
import math
import os
from pathlib import Path
import selectors
import subprocess
import tempfile
import threading
import time

from .models import PROFILE, Diagnostic, Span, ValidationResult
from .profiles import SUPPORTED_STATEMENT_KINDS, qualified_identity

DIAGNOSTIC_KINDS = {
    "CUBRID-S1001": ("syntax", "error"),
    "CUBRID-U1001": ("unsupported", "warning"),
    "CUBRID-U1002": ("unsupported", "warning"),
    "CUBRID-T1001": ("tool", "error"),
    "CUBRID-T1002": ("tool", "error"),
    "CUBRID-T1003": ("tool", "error"),
}


def _trivia_only(text):
    """Unreported gaps may contain only separators and ordinary closed comments."""
    index = 0
    while index < len(text):
        if text[index] in " \t\r\n\v\f;":
            index += 1
        elif text.startswith(("--", "//"), index):
            if text.startswith(("--+", "//+"), index):
                return False
            end = text.find("\n", index + 2)
            index = len(text) if end < 0 else end + 1
        elif text.startswith("/*", index):
            end = text.find("*/", index + 2)
            if (text.startswith(("/*+", "/*!"), index) or end < 0
                    or 0 <= text.find("/*", index + 2) < end):
                return False
            index = end + 2
        else:
            return False
    return True


@dataclass(frozen=True)
class WorkerConfig:
    executable: Path
    runtime_prefix: Path
    manifest: Path | None = None
    timeout: float = 5.0
    max_document_bytes: int = 8 * 1024 * 1024
    max_response_bytes: int = 16 * 1024 * 1024
    max_diagnostics: int = 256

    def __post_init__(self):
        for name in ("executable", "runtime_prefix"):
            value = Path(getattr(self, name))
            if not value.is_absolute():
                raise ValueError(f"{name} must be an explicit absolute path")
            object.__setattr__(self, name, value)
        manifest = Path(self.manifest) if self.manifest is not None else self.executable.parent / "manifest.json"
        if not manifest.is_absolute():
            raise ValueError("manifest must be an explicit absolute path")
        object.__setattr__(self, "manifest", manifest)
        if type(self.timeout) not in (int, float) or not math.isfinite(self.timeout) or not 0 < self.timeout <= 300:
            raise ValueError("timeout must be positive and at most 300 seconds")
        for name, ceiling in (("max_document_bytes", 8 * 1024 * 1024),
                              ("max_response_bytes", 16 * 1024 * 1024), ("max_diagnostics", 256)):
            value = getattr(self, name)
            if type(value) is not int or not 0 < value <= ceiling:
                raise ValueError(f"{name} must be positive and at most {ceiling}")


class WorkerFailure(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


class NativeWorker:
    """Configuration comes from trusted callers; no PATH/runtime discovery.

    Use parse_async in a protocol event loop. The synchronous parse seam is also
    suitable for an executor. Neither path retries a failed request.
    """

    def __init__(self, config: WorkerConfig, profile: str = PROFILE):
        self.config, self.profile = config, profile
        self.process = None
        self._stderr = None
        self._lock = threading.RLock()
        self._process_lock = threading.Lock()
        self._async_lock = asyncio.Lock()
        self._id = 0
        self._identity = None
        self._failure = None
        self._closed = False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def _terminate(self):
        with self._process_lock:
            process = self.process
            if process is not None:
                if process.poll() is None:
                    process.kill()
                process.wait(timeout=1)

    def _dispose(self):
        self._terminate()
        with self._process_lock:
            if self.process is not None:
                for stream in (self.process.stdin, self.process.stdout):
                    stream.close()
                self.process = None
            if self._stderr is not None:
                self._stderr.close()
                self._stderr = None

    def close(self):
        if self._lock.acquire(blocking=False):
            try:
                if not self._closed and self.process is not None and self._identity is not None:
                    try:
                        response = self._request("shutdown", _timeout=0.25)
                        if response.get("status") == "closed":
                            self.process.wait(timeout=0.25)
                    except (WorkerFailure, OSError, subprocess.TimeoutExpired):
                        pass  # A failed shutdown still ends and reaps this owned PID.
                self._closed = True
                self._dispose()
            finally:
                self._lock.release()
        else:
            self._closed = True
            self._terminate()
            with self._lock:
                self._dispose()

    def _start(self):
        if self._closed:
            raise WorkerFailure("CUBRID-T1002", "worker has been closed")
        try:
            self._stderr = tempfile.TemporaryFile()
            with self._process_lock:
                if self._closed:
                    raise WorkerFailure("CUBRID-T1002", "worker has been closed")
                self.process = subprocess.Popen(
                    [str(self.config.executable), "--manifest", str(self.config.manifest)],
                    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self._stderr,
                    env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "HOME": "/nonexistent"},
                    cwd="/", close_fds=True,
                )
            os.set_blocking(self.process.stdin.fileno(), False)
            os.set_blocking(self.process.stdout.fileno(), False)
        except OSError as error:
            raise WorkerFailure("CUBRID-T1001", f"native worker unavailable: {error}") from error

    def _request(self, method, _timeout=None, **values):
        self._id += 1
        request = {"protocolVersion": 1, "id": self._id, "method": method, **values}
        wire = json.dumps(request, ensure_ascii=False, separators=(",", ":")).encode("utf-8") + b"\n"
        process = self.process
        deadline = time.monotonic() + (self.config.timeout if _timeout is None else min(_timeout, self.config.timeout))
        sent = 0
        received = bytearray()
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdin, selectors.EVENT_WRITE)
            selector.register(process.stdout, selectors.EVENT_READ)
            while True:
                if self._closed or process.poll() is not None:
                    raise WorkerFailure("CUBRID-T1002", "native worker closed or exited")
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise WorkerFailure("CUBRID-T1002", "native worker deadline exceeded")
                events = selector.select(min(remaining, 0.05))
                for key, mask in events:
                    if mask & selectors.EVENT_WRITE:
                        try:
                            sent += os.write(key.fd, wire[sent:sent + 65536])
                        except BlockingIOError:
                            continue
                        except OSError as error:
                            raise WorkerFailure("CUBRID-T1002", "native worker input pipe failed") from error
                        if sent == len(wire):
                            selector.unregister(process.stdin)
                    if mask & selectors.EVENT_READ:
                        try:
                            chunk = os.read(key.fd, min(65536, self.config.max_response_bytes + 1 - len(received)))
                        except BlockingIOError:
                            continue
                        if not chunk:
                            raise WorkerFailure("CUBRID-T1002", "native worker exited without a complete response")
                        received.extend(chunk)
                        if len(received) > self.config.max_response_bytes:
                            raise WorkerFailure("CUBRID-T1002", "native response exceeds configured byte limit")
                        if b"\n" in received:
                            first, remainder = received.split(b"\n", 1)
                            if remainder or sent != len(wire):
                                raise WorkerFailure("CUBRID-T1002", "unsolicited native worker output")
                            try:
                                response = json.loads(first.decode("utf-8", errors="strict"))
                            except (ValueError, UnicodeError) as error:
                                raise WorkerFailure("CUBRID-T1002", "malformed native worker response") from error
                            if (not isinstance(response, dict) or type(response.get("protocolVersion")) is not int or response["protocolVersion"] != 1
                                    or type(response.get("id")) is not int or response["id"] != self._id):
                                raise WorkerFailure("CUBRID-T1002", "native response protocol/id mismatch")
                            return response

    @staticmethod
    def _reported_failure(response):
        code, message = response.get("code"), response.get("message")
        if (response.get("status") != "tool-error" or not isinstance(code, str)
                or code not in ("CUBRID-T1001", "CUBRID-T1002", "CUBRID-T1003")
                or not isinstance(message, str)):
            return WorkerFailure("CUBRID-T1002", "malformed native worker failure")
        return WorkerFailure(code, message)

    def initialize(self):
        with self._lock:
            if self._failure is not None:
                raise self._failure
            if self._identity is not None:
                if self._closed:
                    raise WorkerFailure("CUBRID-T1002", "worker has been closed")
                return copy.deepcopy(self._identity)
            try:
                self._start()
                identity = self._request("initialize", profile=self.profile,
                                         runtimePrefix=str(self.config.runtime_prefix))
                if identity.get("status") == "unsupported" and identity.get("code") == "CUBRID-U1001":
                    raise WorkerFailure("CUBRID-U1001", "unknown or mismatched parser profile")
                if identity.get("status") != "ready":
                    raise self._reported_failure(identity)
                expected = qualified_identity(self.profile, self.config.runtime_prefix)
                if any(type(identity.get(key)) is not type(value) for key, value in expected.items()):
                    raise WorkerFailure("CUBRID-T1002", "malformed native worker identity")
                if any(json.dumps(identity[key], sort_keys=True) != json.dumps(value, sort_keys=True)
                       for key, value in expected.items()):
                    raise WorkerFailure("CUBRID-U1001", "worker identity differs from qualified profile")
                try:
                    manifest_digest = hashlib.sha256(self.config.manifest.read_bytes()).hexdigest()
                except OSError as error:
                    raise WorkerFailure("CUBRID-T1001", "qualification manifest unavailable") from error
                if identity.get("manifestDigest") != manifest_digest:
                    raise WorkerFailure("CUBRID-T1002", "worker qualification manifest digest mismatch")
                self._identity = identity
                return copy.deepcopy(identity)
            except WorkerFailure as error:
                self._failure = error
                self._dispose()
                raise

    def _result(self, response, text):
        status = response.get("status")
        if status not in ("valid", "syntax-error", "unsupported", "tool-error"):
            raise WorkerFailure("CUBRID-T1002", "native result has invalid status")
        if "diagnostics" not in response:
            raise self._reported_failure(response)
        if response.get("syntaxSettingsUnchanged") is not True:
            raise WorkerFailure("CUBRID-T1002", "native result does not verify qualified syntax settings")
        if response.get("manifestDigest") != self._identity["manifestDigest"]:
            raise WorkerFailure("CUBRID-T1002", "native result manifest identity mismatch")
        if (response.get("profile") != self.profile or response.get("coverage") not in ("complete", "partial", "none")
                or not isinstance(response["diagnostics"], list) or not isinstance(response.get("statementKinds"), list)):
            raise WorkerFailure("CUBRID-T1002", "native result has invalid profile or coverage")
        if len(response["diagnostics"]) > self.config.max_diagnostics:
            raise WorkerFailure("CUBRID-T1002", "diagnostic limit exceeded; result truncated")
        diagnostics = []
        try:
            for value in response["diagnostics"]:
                span = Span(value["span"]["start"], value["span"]["end"])
                if span.end > len(text) or value["rangePrecision"] not in ("statement", "token", "exact"):
                    raise ValueError("invalid diagnostic span")
                if value["category"] not in ("syntax", "unsupported", "tool") or value["severity"] not in ("error", "warning"):
                    raise ValueError("invalid diagnostic category")
                if not isinstance(value["code"], str) or not isinstance(value["message"], str):
                    raise ValueError("invalid diagnostic text")
                if DIAGNOSTIC_KINDS.get(value["code"]) != (value["category"], value["severity"]):
                    raise ValueError("diagnostic code contradicts category/severity")
                diagnostics.append(Diagnostic(value["code"], value["severity"], value["message"], span,
                                              value["rangePrecision"], value["category"]))
            if any(kind not in SUPPORTED_STATEMENT_KINDS for kind in response["statementKinds"]):
                raise ValueError("unqualified statement kind")
            decisions, observations = response["coverageDecisions"], response["nativeObservations"]
            if not isinstance(decisions, list) or not isinstance(observations, list):
                raise ValueError("invalid native coverage observations")
            admitted, unsupported, last_end = 0, 0, 0
            for decision in decisions:
                span = Span(decision["start"], decision["end"])
                if (span.start < last_end or span.start == span.end or span.end > len(text)
                        or not _trivia_only(text[last_end:span.start]) or type(decision["admitted"]) is not bool):
                    raise ValueError("invalid coverage decision")
                last_end = span.end
                if decision["admitted"]:
                    admitted += 1
                else:
                    categories = {d.category for d in diagnostics if d.span == span}
                    if not categories:
                        raise ValueError("rejected coverage has no diagnostic")
                    unsupported += "unsupported" in categories
            if not _trivia_only(text[last_end:]):
                raise ValueError("coverage omitted nontrivial source text")
            expected_coverage = "partial" if unsupported and admitted else "none" if unsupported else "complete"
            if response["coverage"] != expected_coverage or len(observations) != admitted:
                raise ValueError("coverage contradicts admitted statements")
            if bool(unsupported) != any(d.category == "unsupported" for d in diagnostics):
                raise ValueError("coverage contradicts unsupported diagnostics")
            successes = 0
            for observation in observations:
                for key in ("hasTree", "hasInternalError", "hasError"):
                    if type(observation[key]) is not bool:
                        raise ValueError("invalid native error flag")
                for key in ("treeCount", "errorCount", "partialStackCount"):
                    if type(observation[key]) is not int or observation[key] < 0:
                        raise ValueError("invalid native observation count")
                if type(observation["nativeErrorId"]) is not int:
                    raise ValueError("invalid native error-manager observation")
                if observation["hasTree"] != (observation["treeCount"] > 0):
                    raise ValueError("native tree flag contradicts tree count")
                if (observation["treeCount"] > 1 or (not observation["errorCount"]
                        and observation["treeCount"] != 1)) and not any(d.category == "tool" for d in diagnostics):
                    raise ValueError("missing or partial native trees have no tool diagnostic")
                internal = (observation["hasInternalError"] or observation["nativeErrorId"] != 0
                            or (observation["hasError"] and not observation["errorCount"]))
                if internal and not any(d.category == "tool" for d in diagnostics):
                    raise ValueError("internal error has no tool diagnostic")
                if observation["errorCount"] and not any(d.category in ("syntax", "tool") for d in diagnostics):
                    raise ValueError("native errors have no diagnostic")
                if (not internal and not observation["errorCount"] and observation["hasTree"]
                        and observation["treeCount"] == 1):
                    successes += 1
            if len(response["statementKinds"]) != successes:
                raise ValueError("statement kinds contradict native success counts")
        except (KeyError, TypeError, ValueError) as error:
            raise WorkerFailure("CUBRID-T1002", "malformed native diagnostics") from error
        diagnostics = tuple(sorted(set(diagnostics), key=lambda d: (d.span.start, d.span.end, d.code)))
        expected_status = ("tool-error" if any(d.category == "tool" for d in diagnostics) else
                           "syntax-error" if any(d.category == "syntax" for d in diagnostics) else
                           "unsupported" if any(d.category == "unsupported" for d in diagnostics) else "valid")
        if status != expected_status or (status == "valid" and response["coverage"] != "complete"):
            raise WorkerFailure("CUBRID-T1002", "native status contradicts diagnostics/coverage")
        return ValidationResult(status, response["coverage"], self.profile, diagnostics, tuple(response["statementKinds"]))

    def parse(self, text: str) -> ValidationResult:
        with self._lock:
            try:
                try:
                    encoded = text.encode("utf-8", errors="strict")
                except (AttributeError, UnicodeError) as error:
                    raise WorkerFailure("CUBRID-T1003", "input must contain valid Unicode scalars") from error
                if b"\0" in encoded or len(encoded) > self.config.max_document_bytes:
                    raise WorkerFailure("CUBRID-T1003", "input contains NUL or exceeds the document byte limit")
                self.initialize()
                return self._result(self._request("parse", text=text), text)
            except WorkerFailure as error:
                if error.code not in ("CUBRID-T1003", "CUBRID-U1001"):
                    self._failure = error
                    self._dispose()
                category = "unsupported" if error.code == "CUBRID-U1001" else "tool"
                return ValidationResult("unsupported" if category == "unsupported" else "tool-error", "none", self.profile,
                    (Diagnostic(error.code, "warning" if category == "unsupported" else "error", str(error),
                                Span(0, len(text) if isinstance(text, str) else 0), "statement", category),))

    async def parse_async(self, text: str) -> ValidationResult:
        async with self._async_lock:
            task = asyncio.create_task(asyncio.to_thread(self.parse, text))
            try:
                return await asyncio.shield(task)
            except asyncio.CancelledError:
                self._closed = True
                self._terminate()
                task.cancel()
                with suppress(asyncio.CancelledError):
                    await task
                raise
