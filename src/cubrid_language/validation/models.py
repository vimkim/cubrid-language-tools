"""Immutable validation values shared by command-line and editor adapters."""

from dataclasses import dataclass

from cubrid_language.models import Span


PROFILE = "cubrid-11.5.0.2704-cc94778"


@dataclass(frozen=True)
class Diagnostic:
    code: str
    severity: str
    message: str
    span: Span
    range_precision: str
    category: str

    def to_dict(self):
        return {"code": self.code, "severity": self.severity, "message": self.message,
                "span": {"start": self.span.start, "end": self.span.end},
                "rangePrecision": self.range_precision, "category": self.category}


@dataclass(frozen=True)
class ValidationResult:
    status: str
    coverage: str
    profile: str
    diagnostics: tuple[Diagnostic, ...] = ()
    statement_kinds: tuple[str, ...] = ()

    def to_dict(self):
        return {"status": self.status, "coverage": self.coverage, "profile": self.profile,
                "diagnostics": [d.to_dict() for d in self.diagnostics],
                "statementKinds": list(self.statement_kinds)}
