# Qualified offline parser worker

This separately built Linux x86-64 executable qualifies only
**cubrid-11.5.0.2704-cc94778**, with coverage revision
**bounded-query-dml-schema-engineer-v3**.
It checks parser-stage syntax without a database connection or submitted-SQL
execution. Bounded SELECT, joins, integer arithmetic/comparisons, nonrecursive
CTEs/subqueries, INSERT, UPDATE, DELETE, MERGE and the original CREATE SERIAL
subset are qualified. Bounded TABLE/VIEW/INDEX/SERIAL DDL, EVALUATE,
UPDATE STATISTICS, SHOW TRACE, SET SYSTEM PARAMETERS, SET TRACE and
COMMIT/ROLLBACK/SAVEPOINT are also qualified.
DESCRIBE/DESC/EXPLAIN and SHOW COLUMNS remain unsupported: their shared helper
reports a native not-connected error in this exact offline runtime.
The user accepted these exclusions for the first offline profile on 2026-10-29.
A separately qualified parser-only backend remains later work.
Functions, hints and unknown features return unsupported
coverage before native parsing. An admitted token
sequence must still pass the native parser, error flags and tree checks.

Read [AUDIT.md](AUDIT.md) for the pinned-source reachable-action/settings review,
[QUERY_DML_AUDIT.md](QUERY_DML_AUDIT.md) for query/DML limits,
[SCHEMA_ENGINEER_AUDIT.md](SCHEMA_ENGINEER_AUDIT.md) for schema/engineer bounds
and the concrete description blocker,
[notices/README.md](notices/README.md) for retained licenses and runtime inventory,
and [qualification/results.json](qualification/results.json) for actual fixtures
and trace limits. The Python distribution contains the adapter; native binaries
and CUBRID runtime assets remain separately supplied trusted inputs.

Names and relations are syntactic references only. Nonexistent tables can pass;
object existence, types, privileges and row effects require later server stages.
The profile admits simple quoted names, but excludes embedded quote/escape/dot
spellings, CTE column lists and table-alias column lists. ORDER/GROUP/LIMIT,
set operations, recursive CTEs, INSERT SET/default/duplicate-key clauses, MERGE
DELETE clauses, functions, serial values, host/session parameters and DBLINK
remain unsupported. `SET (` is excluded, including a tuple assignment directly
after SET. See the audit for the complete token/adjacency boundary.

## Reproduce this host qualification

Prerequisites are Python 3.10+, a C++17 compiler, OpenSSL development headers and
libcrypto, explicit matching CUBRID source/generated headers/library/runtime
assets, and strace for trace qualification. Native tests require the built worker
and manifest; missing prerequisites are failures, never skipped passes. No CUBRID
source setup, database initialization or daemon startup is needed.

From this repository's checkout:

~~~sh
just build-native-parser \
  /home/vimkim/gh/cubrid-rust/reference-cubrid-cc947788 \
  /home/vimkim/gh/cb/develop/build_preset_debug_gcc \
  /home/vimkim/gh/cb/develop/build_preset_debug_gcc/cs/libcubridcs.so.11.5 \
  /home/vimkim/.cub/install/develop/debug
just test-native-parser
python3 native/parser-worker/qualify.py \
  --build native/parser-worker/build \
  --output native/parser-worker/qualification
just test
just build
~~~

The source distribution also includes the scripts, worker source, coverage
headers, notices and tests. Where the checkout's just recipes are unavailable,
invoke build.py with the same four explicit inputs:

~~~sh
python3 native/parser-worker/build.py \
  --source /absolute/pinned/source \
  --generated /absolute/matching/generated \
  --library /absolute/pinned/libcubridcs.so.11.5 \
  --runtime-prefix /absolute/qualified/runtime
PYTHONPATH=src python3 -m unittest discover -s tests/native_parser -v
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_validation_*.py' -v
~~~

The helper refuses a different source commit, tracked source edits, generated
version, library digest or platform. It records all source headers, explicit
build headers, actual compiler inputs, exact compiler invocation/version,
resolved runtime dependency digests, runtime catalogs/timezone data, settings,
coverage revision and worker-source hashes. The manifest digest is embedded in
the executable. Runtime verification rejects a missing or changed manifest or
asset before parsing; initialization checks the native-returned version and
explicit settings too. The adapter compares the configured manifest's digest
with initialize and every parse result. The generated build directory is
ignored and excluded from source distributions.

This host's library is SHA-256
56eb36e9a46e3b6f5258974b25085b81d1679430618041343e4d979704822b33,
from source cc947788d3b7dc402f46192d0f3299ddcc8563ba. Current develop source
is newer and must not supply substitute source headers. Other 11.5 builds,
11.4, Windows and macOS need separate qualification. An existing manifest is
host-specific: copying it does not qualify another library, path or installation.

A worker built for an earlier coverage revision can share this profile/version
name and still fail the adapter's identity check with **CUBRID-U1001 unsupported**.
Rebuild the trusted worker and its manifest from the same current checkout with
the four exact inputs above, then rerun the native recipe and qualification
corpus. Keep the binary and its embedded-digest manifest together. Do not edit an
old manifest, select a nearby version, or suppress the identity mismatch.

## Install and use

Install the Python wheel in the caller's environment (no mandatory Python runtime
dependencies). Build the worker separately, retain its manifest and notices, and
configure absolute paths through trusted user/editor settings or explicit CLI
flags. Project files cannot select executables. Nothing searches PATH for a
worker, connects to a server, downloads assets, or installs a runtime implicitly.

For a same-host native install, copy parser-worker, manifest.json and
build-evidence.json from the build directory to a trusted directory and keep the
notices and this audit beside them. Keep the qualified runtime inputs at their
manifest paths and read-only. Moving the native/runtime inputs requires rebuilding
and rerunning qualification with the new explicit paths; editing the manifest
breaks its embedded digest. Do not install a test-only fault build.

The adapter API for this ticket is:

~~~python
from pathlib import Path
from cubrid_language.validation import NativeWorker, WorkerConfig

config = WorkerConfig(
    executable=Path('/absolute/trusted/parser-worker'),
    runtime_prefix=Path('/absolute/qualified/runtime'),
    # manifest defaults to manifest.json beside the executable
)
with NativeWorker(config) as worker:
    result = worker.parse("SELECT '가😀', -10, NULL;")
    print(result.status, result.coverage, result.to_dict())
~~~

Use await worker.parse_async(text) from an event loop. Blocking pipe I/O runs in
an executor thread; one lock serializes requests. A cancelled request closes
that client, so construct a new configured client for later work. The higher-level
[Validator, CLI](../../docs/lint-cli.en.md), and [LSP](../../docs/lsp.en.md) are implemented adapters.

The production process accepts UTF-8 JSON lines with protocolVersion=1 and an
integer id. initialize selects the exact profile; parse accepts text; shutdown
closes it. Replies echo the version/id. There is no execute, connect, file include,
shell, listener, localhost port or shared daemon operation. The protocol is an
internal worker boundary; consumers use the Python adapter.

## Failure and resource behavior

Unknown profiles are U1001 unsupported results. Missing worker/manifest/assets
are T1001. Native crashes, deadlines, malformed or contradictory responses,
manifest/asset digest failures, internal flags and incomplete trees are T1002.
Invalid Unicode/UTF-8, NUL, configuration and document-size failures are T1003.
Ordinary parser errors in these audited productions are S1001. Each admitted
observation includes an integer nativeErrorId. Any nonzero native error-manager
value yields T1002, even when a tree has no parser error. Every parse request
checks the actual qualified syntax settings before and after parsing. Syntax and unsupported
diagnostics can coexist; priority is tool-error, syntax-error, unsupported, valid.
Empty text passes only after runtime/profile availability succeeds.

Defaults are 5 seconds per request, 8 MiB UTF-8 documents, 16 MiB replies and
256 diagnostics. Trusted callers may lower those limits or set a finite positive
deadline up to 300 seconds; byte/diagnostic overrides cannot exceed the defaults.
The native frame bound is 64 MiB to allow JSON escaping, and its address space is
limited to 512 MiB. Hitting a limit yields a tool failure or owned-process failure,
never a truncated pass. Up to 256 ordinary findings fit without truncation. An actual
257th finding causes native truncation, preserving 255 prior findings plus T1002,
with incomplete coverage and an original tail or final-statement span. Lower trusted Python
diagnostic limits apply only after response validation and retain prior findings within the cap.
Diagnostic ranges use original code points. Observed
native columns count UTF-8 bytes and can be missing/negative, so exposed native
errors use statement precision. UTF-16 conversion stays in DocumentMap.

Before dlopen the worker clears inherited settings and creates a private 0700
prefix with configuration, empty database registry, temporary path, built-in-only
locale file and error log. Only catalog/library directories point at qualified
read-only assets. Normal idle close sends shutdown, waits with a 250 ms bound,
and allows the worker to remove that exact private prefix. Timeout, crash,
cancellation or active close uses kill/reap of the owned PID only. Abrupt native
termination can leave its private temporary directory; the client never sweeps
/tmp or signals descendants/unrelated processes.

The retained strace covers network/process/openat calls for 325 listed fixtures:
one worker execution, no descendants, no network calls and no external writable
opens. Ordinary system library/locale files can be read. This observation is
corpus-specific and is not an operating-system sandbox or a proof for other SQL.

## Deterministic internal-error qualification

The native suite calls build.py with --test-internal-error and a separate
--output directory. That build defines CUBRID_PARSER_TEST_INTERNAL_ERROR and sets
the real parser has_internal_error flag immediately after parsing, before
classification. A good tree must still yield T1002 and no successful statement
kind. Its manifest/initialize identity says testOnly=true; the production client
rejects it. The default output refuses the test switch. Production code excludes
the injection at compile time, and production JSON requests have no fault switch.
