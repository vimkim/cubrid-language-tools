"""Configured document validation shared by CLI and editor adapters."""

import threading

from .models import Diagnostic, Span, ValidationResult
from .worker import NativeWorker, WorkerConfig


class Validator:
    """Own a native worker selected only by explicit trusted configuration.

    Both script modes currently use the worker's conservative coverage. Mixed
    CSQL constructs remain unsupported until separately qualified.
    """

    def __init__(self, config: WorkerConfig | None = None):
        self.config = config
        self._worker = None
        self._closed = False
        self._ownership = threading.Lock()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        with self._ownership:
            self._closed = True
            worker = self._worker
        if worker is not None:
            worker.close()

    def validate(self, text, profile, script_mode):
        def failure(code, message):
            return ValidationResult('tool-error', 'none', profile if isinstance(profile, str) else '', (
                Diagnostic(code, 'error', message, Span(0, len(text) if isinstance(text, str) else 0),
                           'statement', 'tool'),))

        if not isinstance(text, str):
            return failure('CUBRID-T1003', 'document text must be a Unicode string')
        try:
            encoded = text.encode('utf-8', errors='strict')
            valid_profile = isinstance(profile, str) and bool(profile) and '\0' not in profile
            if valid_profile:
                profile.encode('utf-8', errors='strict')
        except UnicodeError:
            return failure('CUBRID-T1003', 'input must contain valid Unicode scalars')
        if not valid_profile or script_mode not in ('sql', 'csql'):
            return failure('CUBRID-T1003', 'profile must be nonempty and script mode must be sql or csql')
        if self.config is not None and not isinstance(self.config, WorkerConfig):
            return failure('CUBRID-T1003', 'configuration must be an explicit trusted WorkerConfig')
        limit = self.config.max_document_bytes if self.config is not None else 8 * 1024 * 1024
        if b'\0' in encoded or len(encoded) > limit:
            return failure('CUBRID-T1003', 'input contains NUL or exceeds the document byte limit')
        with self._ownership:
            if self._closed:
                return failure('CUBRID-T1002', 'validator has been closed')
            if self.config is None:
                return failure('CUBRID-T1001', 'trusted parser worker/runtime configuration is required')
            if self._worker is None or self._worker.profile != profile:
                if self._worker is not None:
                    self._worker.close()
                self._worker = NativeWorker(self.config, profile)
            worker = self._worker
        result = worker.parse(text)
        diagnostics = tuple(sorted(dict.fromkeys(result.diagnostics), key=lambda d:
            (d.span.start, d.span.end, d.code, d.message, d.severity, d.range_precision, d.category)))
        return ValidationResult(result.status, result.coverage, result.profile, diagnostics, result.statement_kinds)
