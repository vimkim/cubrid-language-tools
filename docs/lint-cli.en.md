# Offline lint CLI and configured validation

[한국어](lint-cli.md) | **English**

`cubrid-lint` checks files and stdin through the shared `Validator`.
It never executes submitted SQL, CSQL commands, includes, or shell text.
The Python package requires Python 3.10+ with no mandatory Python dependencies.
Strict checks require the separately built, qualified native worker and runtime.
See the [native build and installation guide](../native/parser-worker/README.md).

## Install and check files

Install the Python package in your environment:

```sh
uv pip install .
```

Supply trusted worker and runtime paths explicitly:

```sh
cubrid-lint \
  --parser-worker /absolute/trusted/parser-worker \
  --runtime-prefix /absolute/qualified/runtime \
  --format json first.sql second.csql -
```

`-` reads stdin as bytes exactly once. It can appear only once.
The tool reads each file as bytes and decodes strict UTF-8.
It preserves Unicode, CRLF, whitespace, and path argument spelling.
Inputs larger than 8 MiB, invalid UTF-8, NUL, and unavailable files produce tool errors.
Each failed input still has an ordered document result.
Directories are invalid inputs. The tool does not scan directories or expand globs.

Options are `--profile ID`, `--script-mode sql|csql`, `--format human|json`,
`--config PATH`, `--parser-worker PATH`, and `--runtime-prefix PATH`.
Human format is the default. Both trusted native paths must be supplied together.
Relative explicit native paths use the working directory.
The manifest defaults to `manifest.json` beside the worker.
Project metadata and environment variables cannot select a worker or runtime.
No runtime download, PATH search, or database version probe occurs.
Missing configuration fails explicitly, including for empty files.

## Output and exits

Human diagnostics use `path:line:column: severity code message`.
Lines and code-point columns start at one. Each file also receives a status line.
Statement ranges can include leading whitespace or comments.
A statement diagnostic can therefore point before the first SQL token.

JSON stdout contains one object with these fields:

| Field | Meaning |
| --- | --- |
| `schemaVersion` | Integer `1` |
| `offsetEncoding` | `unicode-codepoints` |
| `documents` | Results in input order, including input failures |
| `status` | Aggregate status |

Each document contains `path`, `profile`, `scriptMode`, `status`, `coverage`,
`diagnostics`, and `statementKinds`.
Diagnostics contain `code`, `severity`, `message`, `category`, `rangePrecision`, and `span`.
A span contains numeric `start` and `end` offsets in the original text.
Spans exclude their end offset. CR and LF each count as one code point.
Native diagnostics currently use statement precision.
Logs and malformed-argument guidance never enter JSON stdout.
Malformed arguments produce stderr guidance and exit 3 before document acquisition.

| Exit | Meaning |
| --- | --- |
| 0 | Every document is fully checked and valid |
| 1 | Syntax errors, with no tool error |
| 2 | Unsupported coverage, with no syntax or tool error |
| 3 | Tool, input, configuration, or argument error |

Priority is tool error, syntax error, unsupported, valid.
Unsupported warnings still prevent exit 0.
There is no `--ignore-unsupported` option.
EOF without a semicolon passes when the selected native parser accepts it.

## Shared project configuration

The optional `.cubrid-language.json` contains metadata only:

```json
{
  "profile": "cubrid-11.5.0.2704-cc94778",
  "scriptMode": "sql",
  "schemaSnapshot": "metadata/schema.json"
}
```

| Key | Accepted value |
| --- | --- |
| `profile` | Nonempty Unicode profile identity |
| `scriptMode` | `sql` or `csql` |
| `schemaSnapshot` | Nonempty Unicode path, or `null` to disable metadata |

All keys are optional. Unknown keys and duplicate keys are invalid.
The loader rejects executable, runtime, command, and credential settings.
Invalid JSON, Unicode, field types, or unreadable configuration produce `CUBRID-T1003`.
An unknown profile remains selected and produces `CUBRID-U1001` when the configured worker checks it.

Each field follows this order:

1. Explicit flags or caller settings.
2. The file supplied by `--config` or `config_path`.
3. The nearest ancestor `.cubrid-language.json`.
4. Defaults.

Discovery starts at each input path's parent directory, using its supplied path identity.
Stdin and untitled documents start at the working directory.
Only the nearest ancestor file participates. Missing fields do not search more distant files.
Every participating file must be valid, even when a higher-priority value overrides its fields.
Each configuration file resolves its own relative snapshot paths against its directory.
Relative caller snapshot paths use the working directory. Paths do not expand `~` or environment variables.

The default profile is `cubrid-11.5.0.2704-cc94778`.
The default mode is `csql` for a `.csql` suffix, ignoring suffix case.
Other paths and stdin default to `sql`.
`schemaSnapshot` supports offline completion metadata. It does not enable semantic checks in the linter.

## Python interfaces

Trusted callers own the configured validator and close it explicitly or through a context manager:

```python
from pathlib import Path
from cubrid_language.validation import PROFILE, Validator, WorkerConfig

config = WorkerConfig(
    executable=Path('/absolute/trusted/parser-worker'),
    runtime_prefix=Path('/absolute/qualified/runtime'),
)
with Validator(config) as validator:
    result = validator.validate("SELECT '가😀';", PROFILE, 'sql')
    print(result.status, result.to_dict())
```

`validate(text, profile, script_mode)` accepts original Unicode document text only.
Invalid text, profiles, modes, or configuration values produce `CUBRID-T1003`.
An absent `WorkerConfig` produces `CUBRID-T1001`.
Calls after close produce `CUBRID-T1002`. Close is idempotent.
Close can interrupt validation from another thread and prevents later worker creation.
Create a new validator after cancellation or close.
Changing the selected profile closes the previously owned worker.
Native errors and coverage decisions remain library responsibilities.
The result preserves all distinct diagnostics with stable source ordering and status priority.

Reuse metadata resolution for CLI or editor settings:

```python
from cubrid_language.config import resolve_config
from cubrid_language.schema import load_snapshot

settings = resolve_config('query.sql', config_path='settings.json', script_mode='sql')
snapshot = load_snapshot(settings.schema_snapshot)
# Pass snapshot.schema to completion and surface snapshot.availability.
settings = resolve_config('query.sql', schema_snapshot=None)
assert settings.schema_snapshot is None
```

`resolve_config` returns frozen `ResolvedConfig(profile, script_mode, schema_snapshot)`.
Omitting `schema_snapshot` inherits the configured snapshot. Explicit `None` disables it.
An explicit project `schemaSnapshot: null` also disables lower-priority metadata.
`ConfigError` exposes code `CUBRID-T1003`.
Worker configuration remains a separate trusted input.

## Current qualification boundary

This Python stage uses the exact Linux x86-64 CUBRID 11.5 profile identified above.
The [native guide](../native/parser-worker/README.md) defines the worker's current qualified SQL coverage.
SQL mode checks the original SQL document.
CSQL mode also classifies the exact help, exit, and autocommit on/off command lines without execution.
The [batch script guide](scripts.en.md) describes original offsets, command spellings, and conservative recovery for pending SQL and procedural regions.
Unaudited procedures, includes, and shell constructs remain explicit unsupported results.
A syntax pass does not establish object existence, privileges, or server semantics.

For the qualified profile, SHOW and optimizer-hint authoring warnings appear beside native diagnostics. Their category is `authoring`. They do not change the native status or exit code. If the combined diagnostic limit is exceeded, the result is a tool error and includes a truncation message.
