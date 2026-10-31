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

## Independent installed and native verification

Root verified production commit `2e314b1` using a core-only wheel installed into Python 3.10.6.
The installed acquisition module matches the task source byte for byte; `wheel-identity.json` records its SHA-256.
The installed wheel passed all 29 exporter tests with isolated Python imports:

```sh
/home/vimkim/temp/cubrid-schema-standalone-645/wheel-310/bin/python -I -m unittest discover \
  -s /home/vimkim/gh/cubrid-language-tools-standalone-export/tests -p test_schema_export.py -v
```

The wheel and source archive built at `2e314b1` passed `tools/check_artifacts.py`.
The check verified 21 package modules, 19 license files, 204 source files, all three entry points, and six optional-only requirements.
The archives and build log are under `/home/vimkim/temp/cubrid-schema-standalone-645/production-dist` and `build.log`.

Native checks used a separate registered `schema645` database and work environment under `/home/vimkim/temp/cubrid-schema-standalone-645/native`.
The existing dedicated CUBRID `11.5.0.2635` debug installation was reused without changing its binaries.
The ordinary develop database, work environment, Neovim configuration, and installed language tools were preserved.

| Native check | Result |
| --- | --- |
| Original installed exporter with `-S` | Exit 2 and empty stdout, reproducing the missing support. |
| New installed exporter with `-S` as DBA | Exit 0; 76 relations, including `schema_people`, its columns and index, and `schema_people_view`. |
| `--SA-mode` as `SCHEMA_READER` | Exit 0; 47 visible relations, granted table and columns present, ungranted view absent. |
| `-C` and `--CS-mode` while the dedicated server runs | Both succeed with the same fixture metadata. |
| `-S` while that server owns the database | Exit 3, empty stdout, fixed redacted error; a subsequent client/server export still succeeds. |
| `-S` after server and master shutdown with process exit confirmed | Succeeds; fixture is intact, and no owned native process remains. |
| Unchanged Neovim plugin `8160c40` and existing LSP with the new installed exporter | Table/view and alias-column completion, refresh, restricted-user switch, disconnect, private snapshots, and LSP process cleanup pass. |

The headless editor opens `hello.sql` and initially puts `DROP TABLE schema_people;` only in the buffer.
Later catalog checks confirm the fixture remains present. Acquisition does not execute that buffer.
The final editor receipt is `editor-gqmljysh/result.json` under the evidence directory.
Native receipts are `native/standalone-dba.json`, `native/standalone-reader.json`, and `native/service-acceptance.json`.

Rerun the native and editor probes against the preserved fixture with:

```sh
source /home/vimkim/temp/cubrid-schema-standalone-645/native/source/.cub-workenv/env.sh
python3 /home/vimkim/temp/cubrid-schema-standalone-645/native-service-probe.py
python3 /home/vimkim/temp/cubrid-schema-standalone-645/native-editor.py \
  --exporter /home/vimkim/temp/cubrid-schema-standalone-645/wheel-310/bin/cubrid-schema \
  --server /home/vimkim/.local/share/uv/tools/cubrid-language-tools/bin/cubrid-language-server
```

The service probe starts and stops only its dedicated environment and preserves its database.
One immediate post-shutdown attempt reached the five-second acquisition deadline.
The same request later succeeded, and a complete repeat passed after explicitly checking native process exit before reopening the database.
These checks do not guarantee native startup or recovery completes within five seconds; the existing configurable deadline still applies.

## Limitations and ownership

Native/editor evidence covers the dedicated CUBRID 11.5 installation on Linux and Neovim 0.12.5.
This ticket does not rerun the historical native parser or distribution qualification matrix.
The release guard change does not claim a complete installed native release run.

CSQL still receives its actual password transiently in child argv.
POSIX process groups remain required. SIGKILL, descendants that deliberately create another session, and regular-file filesystem stalls retain the original containment limits.
No mandatory dependency, shell invocation, runtime service, database lifecycle operation, implicit acquisition, submitted SQL execution, or consumer change was added.
Main integration, rebase, pushes, publication, and global installation remain outside the implementer's authorization.
