# Export schema metadata

[한국어](schema-export.md) | **English** · [Documentation](README.en.md)

`cubrid-schema export` reads visible catalog metadata through an explicitly selected CSQL connection.
It writes one version 1 JSON snapshot for the existing schema loader and completion interfaces.
The command is included in the core installation and needs no optional Python dependencies.
It requires POSIX process groups and an installed CSQL client with the caller's configured CUBRID environment.

## Export a snapshot

Select a trusted CSQL executable and a client/server database endpoint:

```sh
cubrid-schema export --csql /trusted/cubrid/bin/csql --timeout 5 -- -udba demodb@localhost -C > schema.json
```

Exit 0 means stdout contains one complete snapshot. No partial snapshot is emitted on acquisition failure.
Use the file as the existing `schemaSnapshot` setting. Export into a new temporary file before replacing a last-good snapshot.
Connection selection, credential prompts, caching, and refresh scheduling belong to the caller or editor.
`cubrid.reloadSchema` rereads a file. It does not connect to CSQL or fetch new metadata.
Completion, linting, validation, and language-server startup never trigger this exporter.

For an editor or another process, send one UTF-8 JSON object through stdin, then close stdin:

```text
argv: ["cubrid-schema", "export", "--csql", "/trusted/cubrid/bin/csql", "--timeout", "5", "--request-stdin"]
stdin: {"requestVersion":1,"command":"csql -udba demodb@localhost -C","password":null}
```

Build the JSON in memory. Do not put passwords in shell history or the exporter argument list.
`password` is optional. Null preserves an inline password, or uses an empty password if none is present.
A string overrides the inline password, including an empty string.
CSQL requires its actual batch password through `-p`. The secret is transiently visible in the CSQL child's argument list.
The exporter does not invent a password environment variable or send passwords as SQL.

## Accepted requests

| Input | Meaning |
| --- | --- |
| `--csql PATH` | Trusted executable, default `csql` on PATH. A program token inside the request never selects it. |
| `--timeout SECONDS` | Positive finite deadline, default 5, maximum 300. Includes stdin acquisition and result encoding. |
| `--request-stdin` | Read the JSON envelope. Cannot be combined with connection arguments after `--`. |
| `requestVersion` | Required integer 1. |
| `command` | Required nonempty string, tokenized with `shlex` quoting without expansion. |
| `password` | Optional string or null. |

Direct arguments after `--` enter the same connection parser as the JSON command.
An optional leading `csql` or path ending in `csql` is descriptive only.
The parser accepts `-uNAME`, `-u NAME`, `--user=NAME`, and `--user NAME`, plus the equivalent `-p` and `--password` forms.
Identical duplicate values are accepted. Conflicting duplicates are rejected.
`-C` and `--CS-mode` select client/server mode, which is also the default.
When no user is supplied, CSQL selects its default user.
Use attached or equals syntax for a password that starts with `-`.

Exactly one database endpoint is required. Accepted database and hostname characters are Unicode word characters, dots, and hyphens.
An endpoint can include `@host`, a numeric port, or a bracketed IPv6 host. It cannot start with `-` or contain whitespace or shell operators.
Standalone mode, admin modes, arbitrary SQL, input/output files, unknown flags, and extra operands are rejected before child launch.
No shell is invoked. Project configuration cannot select CSQL executables or contain connection credentials.

Requests are limited to 64 KiB. Unknown or duplicate JSON keys, wrong types, invalid UTF-8, invalid quoting, NUL, and trailing JSON data are rejected.
stdout and stderr from CSQL share a 16 MiB bound. Encoded snapshot JSON has a separate 16 MiB bound.
The exporter rejects any CSQL stderr, nonzero exit, missing identity, inconsistent rows, invalid escapes, and orphan columns or indexes.
CSQL's trailing blank lines are accepted. Other unexpected output fails the export.
An identity-only result is a valid empty visible catalog. A permission or query error is a failure.

| Exit | Meaning |
| --- | --- |
| 0 | Complete snapshot on stdout. |
| 2 | Invalid request or options. |
| 3 | CSQL unavailable, failed acquisition, invalid catalog, output overflow, or unsupported platform. |
| 124 | Deadline exceeded. |
| 130 | Cancellation through SIGTERM, SIGINT, or the importable API. |

Failures produce a fixed, redacted stderr message. Child stderr, exception arguments, commands, and passwords are never relayed.
The exporter starts CSQL in a private temporary working directory to contain `cub.err` and removes it on normal cleanup.
It kills the owned process group and reaps the direct child on success, failure, timeout, and handled cancellation, including after the leader exits.
SIGKILL cannot run cleanup handlers. Process groups do not contain a descendant that deliberately creates another session.
The selected executable is a trusted CSQL client, not an untrusted program sandbox.

## Snapshot contents

The snapshot contains `schemaVersion`, authenticated `user`, database name without host, `relations`, and `users`.
Relations preserve owner, name, CLASS/VCLASS kind, columns, system flag, and indexes.
Names preserve Unicode spelling and decoded tab, newline, and backslash escapes.
The metadata-only `source` object contains `endpoint` and no other fields.
A restricted user's successful snapshot represents visible metadata, not every object in the database.
See the [schema contract](contracts.md#schema-snapshot) for the existing loader behavior.

## Import the adapter

```python
from threading import Event
from cubrid_language.acquisition import acquire_schema, parse_connection, snapshot_json

cancelled = Event()
connection = parse_connection("csql -udba demodb@localhost -C", password=None)
schema = acquire_schema(connection, executable="/trusted/cubrid/bin/csql", timeout=5, cancelled=cancelled)
encoded = snapshot_json(schema, source=connection)
```

`Connection` is immutable, validates its fields, and omits connection details from repr.
`parse_connection` accepts a command string or a list/tuple of already-tokenized arguments.
`acquire_schema` returns the existing immutable `Schema`. It raises `AcquisitionError` with a fixed `code` and redacted message.
Setting the optional `threading.Event` cancels acquisition and cleans up the owned group.
`snapshot_json` also accepts a positive bounded `timeout` and optional cancellation event.
The language core never imports this adapter or acquires metadata implicitly.

The [acceptance report](tickets/reports/schema-export.md) records controlled subprocess tests and the separate CUBRID 11.5 catalog smoke.
This acquisition evidence does not change the exact native parser profile or its qualification.
