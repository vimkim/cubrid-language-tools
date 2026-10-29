"""Configured document validation shared by CLI and editor adapters."""

import threading

from cubrid_language.scripts import classify

from .models import Diagnostic, Span, ValidationResult
from .worker import NativeWorker, WorkerConfig, WorkerFailure


class Validator:
    """Own a native worker selected only by explicit trusted configuration.

    SQL uses the native coverage directly. CSQL additionally classifies batch
    commands and opaque unsupported regions without executing their effects.
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
        from cubrid_language.authoring import authoring_diagnostics
        findings = authoring_diagnostics(text, profile, script_mode)
        with self._ownership:
            if self._closed:
                return self._combine(failure('CUBRID-T1002', 'validator has been closed'), findings, text)
            if self.config is None:
                return self._combine(failure('CUBRID-T1001', 'trusted parser worker/runtime configuration is required'), findings, text)
            if self._worker is None or self._worker.profile != profile:
                if self._worker is not None:
                    self._worker.close()
                self._worker = NativeWorker(self.config, profile)
            worker = self._worker
        result = self._script(worker, text, profile) if script_mode == 'csql' else worker.parse(text)
        return self._combine(result, findings, text)

    def _combine(self, result, findings, text):
        key = lambda d: (d.span.start, d.span.end, d.code, d.message, d.severity, d.range_precision, d.category)
        diagnostics = sorted(set((*result.diagnostics, *findings)), key=key)
        limit = self.config.max_diagnostics if self.config is not None else 256
        if len(diagnostics) > limit:
            native = sorted(set(result.diagnostics), key=lambda d: (d.category != 'tool', d.category != 'syntax', key(d)))
            retained = (native + [d for d in diagnostics if d not in native])[:limit - 1]
            context = '; '.join(f'{d.code}: {d.message}' for d in native)
            message = 'Document diagnostic limit exceeded; result truncated'
            if limit == 1 and context:
                message += '; ' + context
            marker = Diagnostic('CUBRID-T1002', 'error', message, Span(0, len(text)), 'statement', 'tool')
            return ValidationResult('tool-error', result.coverage, result.profile,
                                    tuple(sorted((*retained, marker), key=key)), result.statement_kinds)
        return ValidationResult(result.status, result.coverage, result.profile, tuple(diagnostics), result.statement_kinds)

    def _script(self, worker, text, profile):
        diagnostics, kinds = [], []
        available = True
        try:
            worker.initialize()
        except WorkerFailure as error:
            available = False
            category = 'unsupported' if error.code == 'CUBRID-U1001' else 'tool'
            diagnostics.append(Diagnostic(error.code, 'warning' if category == 'unsupported' else 'error',
                                          str(error), Span(0, len(text)), 'statement', category))
            if error.code == 'CUBRID-U1001':
                return ValidationResult('unsupported', 'none', profile, tuple(diagnostics))
        parts = classify(text)
        checked = False
        incomplete = not available
        for part in parts:
            if part.kind == 'command':
                checked |= available
            elif part.kind == 'unsupported':
                incomplete = True
                diagnostics.append(Diagnostic('CUBRID-U1002', 'warning',
                    'CSQL construct is outside qualified batch coverage', part.span, 'statement', 'unsupported'))
                if part.lexical_error:
                    diagnostics.append(Diagnostic('CUBRID-S1001', 'error',
                        'Unterminated quoted token or comment', part.span, 'statement', 'syntax'))
            elif available:
                result = worker.parse(text[part.span.start:part.span.end])
                diagnostics.extend(Diagnostic(d.code, d.severity, d.message,
                    Span(part.span.start + d.span.start, part.span.start + d.span.end),
                    d.range_precision, d.category) for d in result.diagnostics)
                kinds.extend(result.statement_kinds)
                checked |= result.coverage == 'partial' or (result.coverage == 'complete' and
                    bool(result.statement_kinds or result.diagnostics))
                incomplete |= result.coverage != 'complete' or result.status == 'tool-error'
                if result.status == 'tool-error' or any(d.code == 'CUBRID-U1001' for d in result.diagnostics):
                    available = False
            if len(diagnostics) > self.config.max_diagnostics:
                diagnostics = diagnostics[:self.config.max_diagnostics - 1]
                diagnostics.append(Diagnostic('CUBRID-T1002', 'error',
                    'Document diagnostic limit exceeded; result truncated', part.span, 'statement', 'tool'))
                incomplete = True
                break
        status = ('tool-error' if any(d.category == 'tool' for d in diagnostics) else
                  'syntax-error' if any(d.category == 'syntax' for d in diagnostics) else
                  'unsupported' if any(d.category == 'unsupported' for d in diagnostics) else 'valid')
        coverage = ('partial' if checked else 'none') if incomplete else 'complete'
        return ValidationResult(status, coverage, profile, tuple(diagnostics), tuple(kinds))
