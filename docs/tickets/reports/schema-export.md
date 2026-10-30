# S636 acceptance report

The user wants Neovim schema completion from a selected CSQL connection. This ticket provides the shared explicit acquisition adapter and exporter. The editor owns prompts, connection state, and refresh scheduling.

## Scope and checkout

- Baseline is `ad9d9434f6f8d74b8c44d9cadba0faf2362e6606`.
- Task checkout is `/home/vimkim/gh/cubrid-language-tools-schema-export`, branch `schema/csql-export`, destination `main`.
- The CLI milestone is `bab808198a512c6bda4481c41c5f35a8611a4e13`. Production completion is `c2fe7c63e214fea42fdc2f8ee047085b4173c3d8`, including real CSQL framing and `schemaConfigured`. A final documentation commit records the completed checks.
- The frozen dispatch is `/tmp/cubrid-schema-implementation-EMmkLi/contract.md`. Root authorized one additive LSP result field during integration, `schemaConfigured`, to avoid parsing English availability messages.
- Main integration, remote pushes, deployment, global installation, and csql-future migration are outside this delivery. Root owns work item 636 and the native environment. Item 572 was not changed by this implementer.

## Delivered behavior

`cubrid-schema export` accepts direct argv or a strict version 1 stdin JSON request. One parser owns quoting and connection options. Immutable `Connection` values omit all fields from repr. The command rejects unsafe flags before launching CSQL and emits only fixed redacted errors.

The standard-library-only `cubrid_language.acquisition` adapter returns the existing immutable `Schema`. It owns a fixed catalog UNION with an identity row, visible relations and columns, indexes, users, system flags, and authenticated identity. The snapshot includes only an endpoint in its optional source metadata. CSQL executes in a private temporary working directory.

The adapter bounds aggregate child output and encoded JSON independently to 16 MiB. The CLI bounds request input to 64 KiB. One monotonic deadline covers stdin, child acquisition, decoding, serialization, and stdout publication. Selectors drain child stdout and stderr. Every termination path kills the owned POSIX process group and reaps the immediate child, including successful leader exit and cancellation through the importable API.

The CLI writes serialized UTF-8 bytes to stdout with bounded nonblocking writes. It checks cancellation and the deadline during and after publication. Request, acquisition, parse, and serialization failures leave stdout empty. An interrupted output stream can contain partial JSON and exits nonzero. Consumers accept a snapshot only after exit 0 and complete valid JSON. Diagnostic writes are redacted and best effort when stderr is full or closed.

`cubrid.reloadSchema` now reports boolean `schemaConfigured` from the resolved configuration path. This is independent of successful loading. No settings, precedence, cancellation gates, native worker behavior, or completion logic changed.

## Failing-before evidence

1. The initial 15 public-interface tests ran before production implementation. They failed because `cubrid_language.schema_cli` and the acquisition API did not exist and the console entry point was absent. The run recorded 58 failed subcases and one import error in `export-before.log`.
2. Root's first real CSQL smoke found an extra trailing blank line in CSQL tabular output. `test_real_csql_catalog_framing` reproduced exit 3 before the correction. It passed after accepting trailing blank lines while retaining strict nonblank row validation. `export-native-before.log` records the failure.
3. `test_public_api_invalid_values_and_serialized_output_limit` exposed `OverflowError` from a huge Python integer timeout. Boundary validation now rejects out-of-range values before float conversion. `export-timeout-before.log` records the failure.
4. The framed LSP test `test_reload_reports_configured_schema_even_when_the_file_is_missing` failed with missing `schemaConfigured`. The passing test distinguishes omitted paths, missing project paths, explicit null, and missing trusted paths. `schema-configured-before.log` records the failure.
5. Independent real-process probes found the CLI alive after its output deadline and SIGTERM. Draining stdout later returned exit 0 in both cases. New subprocess tests at commit `77a48e4` reproduced four stalled-pipe timeouts, exit 0 after late draining for both timeout and cancellation, and exit 120 on a closed stdout. Logs are `stdout-red.log` and `late-reader-red.log`.

All temporary logs live under `/tmp/cubrid-schema-implementation-EMmkLi`.

## Verification

The controlled executable in `tests/test_schema_export.py` records actual argv and cwd and emits controlled catalog bytes. Assertions exercise the CLI as a subprocess and the importable API with a real child process. No internal process helper is mocked.

The suite covers original `-udba demodb -C` arguments, trusted executable selection, shell-style quoting without expansion, password overrides, strict JSON envelopes, Unicode and escaped names, completion from exported metadata, identity-only catalogs, malformed rows, query errors with exit zero, nonzero exit, stdout/stderr flood and aggregate limits, missing executable, private cwd cleanup, deadline while stdin stays open, timeout, both termination signals, API cancellation, and descendants that hold pipes after their leader exits. It also covers stalled and closed output, late readers, and a full merged stderr/stdout pipe. Process checks treat a zombie as stopped and verify that no owned process remains running.

Completed checks on the original production commit `c2fe7c63e214fea42fdc2f8ee047085b4173c3d8`:

| Check | Result |
| --- | --- |
| Python 3.14 editable default suite, `python -m unittest discover -s tests -v` | 146 passed. |
| Python 3.14 focused exporter suite, `python -m unittest discover -s tests -p test_schema_export.py -v` | 19 passed after the final production edit. |
| Python 3.14 framed LSP suite, `python -m unittest discover -s tests/lsp -v` | 35 passed. |
| Python 3.10.6 wheel, no-dependencies installation, default suite with `-I` | 146 passed. |
| `uv build --out-dir /tmp/cubrid-schema-implementation-EMmkLi/schema-dist` | Wheel and source archive built. |
| `tools/check_artifacts.py` with those archives | All 21 package modules, 19 license files, all three entry points, optional-only dependency declarations, and included source bytes matched. |
| Python 3.10 installed `cubrid-schema export` command with the native-output fixture | Direct console export passed; metadata inventory contained only this package. |
| New documentation links and `git diff --check` | Passed. |

The Python 3.14 interpreter is `/tmp/cubrid-schema-implementation-EMmkLi/venv/bin/python`. The isolated installed-wheel interpreter is `/tmp/cubrid-schema-implementation-EMmkLi/export-wheel-310/bin/python`. The wheel suite ran from this checkout against the installed package with `-I`; child export requests used temporary working directories. Logs are `export-core-final.log`, `export-focused-final.log`, `export-lsp-final.log`, and `export-wheel-310.log`.

The stdout correction is production commit `6be5d558efce6e5045d8f7122d4532e4e975192f`, following the failing tests at `77a48e4`. After the correction, the Python 3.14 default suite passed 149 tests and the exporter suite passed 22 tests. The Python 3.10 core-only installed wheel passed all 22 exporter tests with `-I`. The installed `cubrid-schema` command returned valid JSON with 5,000 relations, then exited 124 on a stalled merged pipe and 130 on SIGTERM with that pipe stalled. Its environment contained only `cubrid-language-tools`. Logs are `stdout-core-green.log`, `stdout-focused-green.log`, and `stdout-wheel-focused.log` under `/tmp/cubrid-schema-implementation-EMmkLi`.

The corrected wheel and source archive were rebuilt in `stdout-dist` and checked with `tools/check_artifacts.py`. The artifact check compares included source and documentation bytes with this checkout and validates entry points, license files, and optional-only dependencies.

## Real CSQL evidence

Root ran the actual exporter against its dedicated CUBRID `11.5.0.2635 debug_gcc` installation and newly initialized `testdb`. The selected environment is `/tmp/cubrid-schema-implementation-EMmkLi/native/source/.cub-workenv/env.sh`. This is catalog acquisition evidence, not a change to strict native parser profile `cubrid-11.5.0.2704-cc94778`.

The DBA result contains `schema_people`, `schema_people_view`, and `[고객 정보]`, including columns and `idx_schema_person`. `SCHEMA_READER` sees only its granted `schema_people` fixture and associated columns/index. Both snapshots load through the existing loader, and completion for `SELECT p. FROM DBA.schema_people p` returns `id` and `person_name` at cursor 9.

Root also tested a password-protected `SCHEMA_PASSWORD` user through the stdin request. The correct separate password produced a visible schema. A wrong password exited 3 with empty stdout, and neither password sentinel appeared in stdout or stderr. `native/password-acceptance.json` records those assertions without credential values.

Root retained `native/export-acceptance.json`, `native/export-dba.json`, and `native/export-schema_reader.json`. The committed `tests/fixtures/schema-csql-11.5.json` preserves selected literal lines, including native framing, from `native/exact-query.stdout`. Its `sourceSha256` identifies the complete captured stdout. Selection details are embedded in the fixture.

## Limitations and choices

CSQL requires the actual batch password in its child argv. Exporter stdin avoids putting the secret in the exporter's argv, but does not remove transient CSQL argv exposure. Credentials remain in caller memory until the caller releases them. Snapshots, errors, and repr omit credentials.

Only POSIX process groups are supported. Nonblocking publication bounds waiting for POSIX pipes, but regular-file filesystem stalls are outside that guarantee. A trusted CSQL process that deliberately escapes its group and an exporter killed with SIGKILL cannot be cleaned up by signal handlers. Successful exports require empty CSQL stderr; warnings on stderr therefore fail conservatively. Restricted results describe only visible metadata. Endpoint validation deliberately accepts a bounded connection grammar rather than arbitrary CSQL options.

The acquisition adapter and schema CLI use no optional Python packages. The existing package version remains `0.1.0.dev0`; it does not identify this commit. Historical full native release matrices are not rerun by this ticket. Root owns independent Neovim integration and final review.

Model the Domain shaped the immutable connection boundary and existing Schema reuse. Test Behavior, Not Implementation shaped subprocess and completion assertions. Prove It Works required the installed command, real process-liveness checks, and real CSQL evidence. Comment review was performed directly because this bounded implementer was explicitly prohibited from spawning another agent.
