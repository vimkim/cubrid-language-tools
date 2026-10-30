# Stdio language server

[한국어](lsp.md) | **English**

The optional Python server supplies shared CUBRID completion and offline syntax diagnostics through LSP 3.17.
Editors start one `cubrid-language-server` child process and communicate through standard input/output.
Start the server with no arguments. The server opens no TCP or WebSocket listener.

## Install and start

Install Python 3.10 or later. Install the optional dependency set:

```sh
uv venv --python 3.10 .venv
uv pip install --python .venv/bin/python '.[lsp]'
```

Run these commands from the local checkout. For a wheel, replace `.[lsp]` with its wheel path and append `[lsp]`.
See [installation and release qualification](install.en.md) and [v4 coverage](coverage.en.md).
Configure the editor to execute `cubrid-language-server` with an empty argument list and stdio transport.
Use the exact language ID `cubrid` when the editor opens a document.
Generic `sql` documents do not activate completion or diagnostics.
The [VS Code extension](https://github.com/vimkim/cubrid-vscode) and [Neovim plugin](https://github.com/vimkim/cubrid.nvim) are public alphas. See their repositories for installation and configuration.
The editor packages do not bundle or automatically download the Python server or native runtime. Keyword completion needs the server but not the native parser. Strict offline syntax diagnostics require a qualified worker, matching runtime, and exact profile.

The core and `cubrid-lint` require no Python runtime dependencies.
The server extra pins pygls 2.1.1, lsprotocol 2025.0.0, attrs 25.4.0, cattrs 25.3.0, and typing-extensions 4.15.0.
Python 3.10 also uses exceptiongroup 1.3.1.
Without the extra, starting the installed server with no arguments prints installation guidance to stderr and exits with status 3.

To check the installed distribution version without starting the server, run `cubrid-language-server --version`.
The value `0.1.0.dev0` does not identify the Git commit or native coverage revision. See [paired upgrades](install.en.md#upgrade-the-core-and-worker-together).
Use `cubrid-language-server --help` or `-h` for usage. Each option must stand alone.
These options require neither the optional LSP dependencies nor the native runtime.
A source-only invocation without installed distribution metadata cannot report a version. Install the package first.

## Trusted editor settings

Send this object as `initialize.initializationOptions`:

```json
{
  "cubrid": {
    "parserWorker": "/absolute/trusted/parser-worker",
    "runtimePrefix": "/absolute/qualified/runtime",
    "profile": "cubrid-11.5.0.2704-cc94778",
    "schemaSnapshot": "/absolute/metadata/catalog.json"
  }
}
```

The editor can replace these settings through `workspace/didChangeConfiguration`:

```json
{"settings":{"cubrid":{"schemaSnapshot":null}}}
```

Each configuration notification replaces the previous editor settings.
Omit a field to inherit the project value or default. Set `schemaSnapshot` to `null` to remove cached schema metadata.

| Setting | Meaning |
| --- | --- |
| `profile` | Explicit parser profile, overriding project metadata |
| `scriptMode` | `sql` or `csql`, overriding project metadata and filename defaults |
| `schemaSnapshot` | Optional JSON snapshot path, or `null` to disable metadata |
| `configPath` | Optional explicit project JSON configuration path |
| `parserWorker` | Trusted absolute worker executable path |
| `runtimePrefix` | Trusted absolute matching runtime prefix |
| `workerManifest` | Optional absolute manifest path, defaulting to `manifest.json` beside the worker |
| `workerTimeout` | Positive deadline in seconds, at most 300, default 5 |

Configure `parserWorker` and `runtimePrefix` together.
Build and qualify the worker with the [native instructions](../native/parser-worker/README.md).
The server does not discover executables through PATH, download runtimes, or select executable paths from project files.

File documents use the [shared CLI configuration rules](lint-cli.en.md).
The nearest ancestor `.cubrid-language.json` supplies metadata.
An explicit `configPath` overrides that file. Editor fields have the highest precedence.
Project snapshot paths use the configuration file's directory.
Relative editor paths use the initialization root directory, or the process working directory when no root exists.
Project files can contain only `profile`, `scriptMode`, and `schemaSnapshot`.

The filename default is `csql` for `.csql`, ignoring case, and `sql` for other files.
Untitled documents use `sql` unless the editor explicitly supplies `scriptMode`.
Changing settings cancels old validation and checks each open CUBRID document again.
Invalid configuration produces `CUBRID-T1003` diagnostics and a protocol log message.

## Completion and schema snapshots

Completion calls the shared pure `complete` function with cached schema metadata.
The server uses UTF-16 positions for all clients, including clients that omit encoding capabilities.
It advertises Full synchronization. Send the entire original document text in each change notification.
The server rejects ranged changes and preserves the document.
Completion rejects invalid lines, surrogate interiors, and positions inside CRLF terminators with error `-32602`.
Each completion item has an explicit text edit that replaces the complete token, including its suffix after the cursor.

Optimizer hint comments offer names and selected table arguments. The server advertises `+` as a completion trigger.
SHOW and hint completion cover more forms than native validation. See [completion and native coverage](coverage.en.md).

The optional snapshot uses the [version 1 schema contract](contracts.md#schema-snapshot).
Absent snapshots allow keyword completion.
A configured load failure produces a visible `window/logMessage` notification.
Completion reads the cached metadata without a database connection or file read.

Send `workspace/executeCommand` to refresh configuration and snapshots explicitly:

```json
{"command":"cubrid.reloadSchema"}
```

The result lists each open document's `uri`, `profile`, `scriptMode`, `schemaAvailable`, `stale`, and `availability`.
A failed refresh retains the last valid metadata and reports its stale state through the result and protocol log.
A successful refresh clears the stale state. Explicit `null` removes metadata immediately.
The server does not watch files or obtain catalog data from a database.

## Diagnostics and lifecycle

The server waits 250 ms after an open, full change, or configuration refresh before validating.
It runs the shared `Validator` and owned worker cleanup outside the protocol event loop.
Completion continues while native initialization or parsing is slow, absent, or unsuccessful.
Missing runtime configuration produces `CUBRID-T1001` diagnostics.
Native results retain core codes, severity, category, and range precision.
Each diagnostic publication includes the document version.
For the qualified profile, conservative SHOW and hint warnings use the `authoring` category.
These warnings can accompany unsupported or unavailable native validation and do not certify syntax.
See [authoring warning limits](coverage.en.md#authoring-warnings).

New versions cancel old checks. Superseded results cannot replace current diagnostics.
Closing a CUBRID document publishes an empty list and cancels its owned work.
Cancellation also closes the owned validator, including checks still queued for execution.
`shutdown`, `exit`, and input EOF clean up owned workers.
Normal shutdown followed by exit returns status 0. Exit or EOF without shutdown returns status 1.
Cancelled requests receive the protocol cancellation error `-32800`.
Only framed protocol messages appear on stdout. Server errors use stderr, and worker stderr remains separately captured.

## Headless verification

From the source checkout, run:

```sh
just test
just test-lsp
just test-native-parser
just test-lsp-native
just build
```

`test-lsp` exercises framed stdio with explicit trusted child fixtures and requires the optional extra.
`test-lsp-native` requires this checkout's matching built worker and manifest.
Missing prerequisites fail these mandatory checks. Default tests require neither pygls nor native artifacts.
The historical v3 distribution checks exercised optional and native LSP on Python 3.10 and 3.14.
See [current qualification evidence](install.en.md#qualification-evidence) for the narrower v4 evidence.
Native grammar limits remain those of the [current coverage reference](coverage.en.md).
