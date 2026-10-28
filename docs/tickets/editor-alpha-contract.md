# Editor alpha acceptance contract

Work item 582. User-selected scope is VS Code and Neovim as separate consumers.
Read `docs/spec.md`, `docs/contracts.md`, and `docs/lsp.en.md` before implementing a consumer.
Core baseline is `3bb70e492efe7bcb7de58a801281f7a088a9c39e`.

## User behavior

1. Install a local VSIX or add the local Neovim plugin without changing the user's real editor profile during tests.
2. Open `.csql` as `cubrid` and see lexical highlighting and deterministic indentation.
3. Keep generic `.sql` in its original language until explicitly opted in.
4. Start the configured `cubrid-language-server` through argv without a shell. Expose useful missing-server errors.
5. Complete unfinished SQL through the shared server and apply its entire replacement span, including a suffix after the cursor.
6. Preserve Korean, emoji and CRLF source locations through native editor APIs and UTF-16 LSP positions.
7. Receive real qualified syntax and unsupported diagnostics. Missing native runtime stays visible while keyword completion continues.
8. Load an offline schema snapshot, explicitly reload it, and expose stale/failed reload state without losing the last valid metadata.
9. Replace configuration with the complete effective `{cubrid: ...}` object on every update. Never drop worker/runtime settings during a snapshot-only change.
10. Close documents and stop/reconfigure the consumer without late diagnostics or abandoned owned server/worker processes.

## Trust and ownership

The core owns all completion and validation decisions. Consumers own editor syntax highlighting and indentation only.
Only trusted user/editor configuration chooses server, worker, manifest and runtime paths. Do not obtain executable values from project metadata or an untrusted workspace.
Keep workspace/root behavior explicit and tested. One server's global settings must not silently apply another folder's executable configuration.
Never install or download the native runtime automatically, execute submitted SQL, connect to a database, or start CUBRID daemons.
Local testing uses dedicated editor profiles, temporary workspaces, loopback-only headless servers and owned processes.

## Acceptance evidence

Use public editor interfaces and real host processes. Mocked editor modules and protocol-only clients do not establish editor acceptance.
Keep reusable headless commands, the actual host versions, screenshots where appropriate, native result/range observations, process receipts, package contents and limitations.
Run unit/build checks where meaningful, but verify installable artifacts and real editor behavior before marking criteria complete.
If a minimum supported editor version is not exercised, label it unverified rather than claiming it passed.

Exact dispatch records will bind each consumer ticket to its repository/worktree/commit and the selected architecture.
The coordinator owns central docs, shared acceptance changes, tracker state and the decision trail.
Each implementer owns only its consumer repository and its own output directory.
Local commits are authorized. Integration, remote creation, consumer pushes, publication and deployment retain the user's approval gates.
