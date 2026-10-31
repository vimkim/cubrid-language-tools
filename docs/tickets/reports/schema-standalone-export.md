# S645 acceptance report

`cubrid-schema export` now accepts standalone CSQL requests through the existing version 1 stdin envelope, direct argv, and importable acquisition API.
Client/server mode remains the default. Snapshot `schemaVersion: 1` is unchanged.

## Scope and checkout

The exact baseline is `8f6dbcc5b791c0ca87268315e75ce281f6953639`.
The task checkout is `/home/vimkim/gh/cubrid-language-tools-standalone-export`, branch `schema/standalone-export`, with `main` as the integration destination.
The frozen dispatch is `/home/vimkim/temp/cubrid-schema-standalone-645/dispatch.md`.
The [ticket](../schema-standalone-export.md) records the delivery requirements.
Root owns work-tracker items 645 and 572 and independent native/editor verification.

## Delivered behavior

Immutable `Connection` adds `mode`, constrained to `"CS"` or `"SA"` with `"CS"` as the default.
The existing endpoint, user, and password construction remains valid. All connection fields remain hidden from repr.
The parser accepts `-S` or `--SA-mode`, including repeated aliases, and preserves the existing client/server aliases.
Mixed modes fail in either order before launch. Standalone mode rejects every endpoint with an `@host` suffix, including IPv6 and port forms.

CSQL receives exactly one `-C` or `-S` argument. The exporter does not retry in another mode.
Fixed catalog SQL, credential handling, process containment, bounds, deadlines, cancellation, and snapshot encoding remain shared between modes.
Child stderr and nonzero exits still produce fixed, redacted failures with empty stdout.
The release interface guard now uses conflicting modes as its invalid request.
The bilingual schema export reference and current CLI contract describe the added mode.
Historical S636 acceptance evidence remains scoped to its original commits.

## Failing-before evidence

Tests were added before production changes and committed as `1cf631d`.
With baseline production code, this command ran 29 tests and failed with seven failed subcases and 13 error subcases:

```sh
uv run python -m unittest discover -s tests -p test_schema_export.py -v
```

Both `test_standalone_stdin_request_exports_usable_snapshot` and `test_standalone_direct_arguments_export_usable_snapshot` observed exit 2 for `-S` and `--SA-mode`.
The fixed error was `Invalid schema export request or options.`
`test_standalone_importable_api_selects_mode` failed because `Connection` had no `mode` constructor argument.
The existing client/server, catalog validation, cancellation, and publication checks passed in that run.
The log is `/home/vimkim/temp/cubrid-schema-standalone-645/export-red.log`.

## Verification

The controlled CSQL executable records actual child argv, launch count, cwd, and PID.
Tests exercise real CLI subprocesses and the importable API without mocking the process implementation.
Standalone exports load through `load_snapshot` and provide relation completion through `complete`.
Assertions cover both aliases, exact selected mode, repeated aliases, default client/server compatibility, all conflicting alias pairs in both orders, and standalone host-suffix rejection before launch.
Standalone child failures preserve redaction and empty stdout, make one launch, reap the child, and remove its private cwd.
A standalone timeout kills the leader and its pipe-holding descendant without a mode retry.
Existing cancellation and output publication regressions remain in the focused suite.

| Check | Result |
| --- | --- |
| `uv run python -m unittest discover -s tests -p test_schema_export.py -v` | 29 passed on Python 3.14.0. |
| `uv run python -m unittest discover -s tests -v` | 156 passed on Python 3.14.0. |
| `.venv/bin/cubrid-schema export -- -S -C demodb` | Exit 2 with empty stdout, matching the updated release guard. |
| Changed-document local links and `git diff --check` | Passed. |

The passing logs are `/home/vimkim/temp/cubrid-schema-standalone-645/export-green.log` and `core-green.log` in the same directory.

## Limitations and ownership

The implementer ran controlled subprocess checks, not real standalone CSQL or Neovim.
Root records separate native and unchanged-editor acceptance after independent verification.
This ticket does not rerun the historical native parser or distribution qualification matrix.
The release guard change does not claim a complete installed native release run.

CSQL still receives its actual password transiently in child argv.
POSIX process groups remain required. SIGKILL, descendants that deliberately create another session, and regular-file filesystem stalls retain the original containment limits.
No mandatory dependency, shell invocation, runtime service, database lifecycle operation, implicit acquisition, submitted SQL execution, or consumer change was added.
Main integration, rebase, pushes, publication, and global installation remain outside the implementer's authorization.
