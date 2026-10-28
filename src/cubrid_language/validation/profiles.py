"""The first qualified identity; every additional build needs qualification."""

from types import MappingProxyType

from .models import PROFILE

SOURCE_COMMIT = "cc947788d3b7dc402f46192d0f3299ddcc8563ba"
NATIVE_VERSION = "11.5.0.2704-cc94778"
COVERAGE_REVISION = "bounded-query-dml-schema-engineer-v3"
SUPPORTED_STATEMENT_KINDS = ('PT_SELECT', 'PT_INSERT', 'PT_UPDATE', 'PT_DELETE', 'PT_MERGE', 'PT_CREATE_SERIAL', 'PT_CREATE_ENTITY', 'PT_ALTER', 'PT_DROP', 'PT_CREATE_INDEX', 'PT_ALTER_INDEX', 'PT_DROP_INDEX', 'PT_ALTER_SERIAL', 'PT_DROP_SERIAL', 'PT_EVALUATE', 'PT_UPDATE_STATS', 'PT_SET_SYS_PARAMS', 'PT_QUERY_TRACE', 'PT_COMMIT_WORK', 'PT_ROLLBACK_WORK', 'PT_SAVEPOINT')
SETTINGS = MappingProxyType({
    "charset": "en_US.utf8", "strings_have_no_escapes": False,
    "ansi_quotes": True, "no_backslash_escapes": False, "pipes_as_concat": True,
    "oracle_style_empty_string": False, "query_trace": False,
    "compat_mode": 0, "intl_check_input_string": True, "intl_collation": "utf8_bin",
    "unicode_input_normalization": False, "unicode_output_normalization": False,
    "parser_use_client_charset": True,
})


def qualified_identity(profile, runtime_prefix):
    return {"profile": profile, "testOnly": False, "nativeVersion": NATIVE_VERSION, "sourceCommit": SOURCE_COMMIT,
            "platform": "linux-x86_64", "coverageRevision": COVERAGE_REVISION,
            "runtimePrefix": str(runtime_prefix), "settings": dict(SETTINGS),
            "supportedStatementKinds": list(SUPPORTED_STATEMENT_KINDS)}
