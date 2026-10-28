# LSP implementation preflight

Observed 2026-10-28. This is source/API research for ticket05, not a qualified server result.
The current product stage is the Python PoC. Library/CLI/LSP behavior must stay comparable during later Rust replacements.

## Framework identity

The live [PyPI metadata](https://pypi.org/pypi/pygls/json) and [release page](https://pypi.org/project/pygls/2.1.1/) identify pygls2.1.1 with Python>=3.9.
It requires lsprotocol==2025.0.0, attrs>=24.3.0 and cattrs>=23.1.2.
The websockets extra is optional and is not needed for the selected stdio transport.
Ticket05 must pin its actually tested optional dependency set and keep core/CLI mandatory dependencies empty.
Test Python3.10 and3.14 rather than treating upstream classifiers as qualification.

The [upstream quickstart](https://pygls.readthedocs.io/en/latest/) imports LanguageServer from pygls.lsp.server and types from lsprotocol.
Use start_io for standard input/output. The [run-server guide](https://pygls.readthedocs.io/en/latest/servers/howto/run-a-server.html) describes transport setup.
Do not expose a TCP/WebSocket listener or download a native runtime.

## Lifecycle and encoding traps

The [built-in feature reference](https://pygls.readthedocs.io/en/latest/servers/reference/built-in-features.html) describes lifecycle and workspace updates.
Custom didOpen/didChange/didClose handlers run after the built-in workspace update.
The custom initialize handler runs after workspace creation and before capability construction.
Shutdown is the resource-cleanup point. Cancellation is a built-in JSON-RPC operation rather than a separately replaceable feature handler.

The exact [LanguageServer constructor](https://github.com/openlawlibrary/pygls/blob/v2.1.1/pygls/lsp/server.py#L58-L72) defaults to incremental synchronization.
Pass Full explicitly to match this project's initial contract.

The exact [encoding chooser](https://github.com/openlawlibrary/pygls/blob/v2.1.1/pygls/capabilities.py#L64-L84) supports UTF-8/16/32 and chooses the first compatible client preference.
The [initialize implementation](https://github.com/openlawlibrary/pygls/blob/v2.1.1/pygls/protocol/language_server.py#L124-L176) uses that choice both for Workspace and advertised capabilities.
Therefore a plain initialize feature hook is too late to change workspace creation.
Enforce the project's UTF-16-only initial interface consistently in negotiation, document mapping, edits and diagnostics.
Do not change only the advertised capability while the framework workspace keeps another encoding.
Exercise omitted encodings and UTF-8/UTF-32-first offers in actual stdio tests.
Use DocumentMap for strict original-text conversions, including CRLF and surrogate-interior rejection.

## Public seams to consume

Use ticket03's shared configuration and configured Validator, and ticket04's schema loading/refresh.
The schema module exposes SchemaSnapshot, load_snapshot(path), and refresh_snapshot(path, previous).
Explicit None disables metadata. A failed configured refresh retains last valid schema with an explicit stale message.
The shared config resolver must distinguish an absent schema override from explicit clearing.
Completion stays pure and uses complete(text,cursor,profile,schema).

Keep native work and worker cleanup off the protocol event loop.
Use document versions to discard stale results and clear diagnostics on close.
Coroutine cancellation alone does not stop an executor thread. Explicitly close/cancel the owned validator/worker and test that stale work cannot publish or later spawn a worker.
The [upstream JSON-RPC handler code](https://github.com/openlawlibrary/pygls/blob/v2.1.1/pygls/protocol/json_rpc.py#L166-L223) schedules coroutine and thread handlers differently.
Tests must exercise public stdio requests, completion during a slow native check, cancellation, configuration changes, close and shutdown.
Native CLI/LSP qualification belongs in mandatory native tests when it requires a built worker. Pure/default tests must not require ignored artifacts.
