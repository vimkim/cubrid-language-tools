# Accept legal LSP enum values from real editors

Work item 582 editor-alpha prerequisite. Product baseline is `3bb70e492efe7bcb7de58a801281f7a088a9c39e`.

## Failure and intended behavior

Both real Neovim and vscode-languageclient fail initialize with JSON-RPC `-32602` on legal enum fields.
The coordinator independently reproduced this with capabilities `{}` and trace `off` through a real stdio server.
Evidence is `/home/vimkim/temp/cubrid-editor-alpha-aiYISe/core-initialize-red.json`.
Neovim's full payload is `/home/vimkim/temp/cubrid-editor-alpha-aiYISe/neovim/initialize.json`; the VS Code payload is in `/home/vimkim/temp/cubrid-editor-alpha-aiYISe/vscode/wire-in`.

Legal protocol enum strings and integers must structure through the authoritative lsprotocol types.
Keep strict rejection of malformed primitive fields, boolean-as-integer positions, unknown enum values and invalid parameters.
Do not fix consumers by stripping standard capabilities or implementing custom JSON-RPC transports.

## Scope and acceptance

1. Establish a focused failing public framed-protocol regression before changing product code.
2. Trace the converter dispatch on ordinary primitive targets versus enum subclasses. Check ranked alternatives against runtime evidence.
3. Apply the smallest boundary fix in `src/cubrid_language/lsp_server.py`; preserve the public API, advertised UTF-16/full-sync behavior and zero mandatory core dependencies.
4. Exercise legal string and integer enum values, actual representative editor initialization payloads, and malformed/unknown values. Keep existing strict-position and malformed-notification behavior.
5. Run existing core and LSP checks, the new red/green regression, and real unmodified Neovim initialization if available. The root coordinates full editor reruns.
6. Commit a failing regression first, then the fix/checks and acceptance report. Provide the exact fixed commit and isolated server executable to unblock consumer owners without merging branches.

Own `strict_converter` and focused protocol tests plus `docs/tickets/reports/editor-lsp-wire-enums.md`.
No native, packaging, recipe, formal-model or consumer code edits. Ask the coordinator before expanding the scope.
Do not weaken existing validation or treat malformed input as successful initialization.
Use pinned existing optional dependencies in a task-owned environment. Keep debug instrumentation out of committed code.
Local commits are authorized. No rebase/integration, push, publication or deployment in this ticket.
