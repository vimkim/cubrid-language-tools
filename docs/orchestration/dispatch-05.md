# Central ticket 05 dispatch

Baseline: `75d550026bddb9b3022263cc99820c4c015e3e65`. Branch: `central/ticket-05`.
Checkout: `/home/vimkim/gh/cubrid-language-tools-05`.
Destination: `implement/central-engine` in the coordinator checkout.

Read AGENTS.md, docs/spec.md, contracts.md, execution.md, tickets/05-lsp.md, orchestration/lsp-preflight.md,
and integrated reports03/04. Read the TDD skill. Use one fresh context for this ticket.
The user gave standing approval for all planned local ticket integrations; root still performs committed review and serialized merges. Do not ask ticket-merge permission.
The current scope is the Python PoC. Later Rust replacement/formatting/consumer products stay in the product roadmap.

## Ownership

Own the optional stdio LSP adapter, entry-point bootstrap, protocol tests and Korean/English LSP guides.
The packaging edit slot now belongs only to you for optional dependency pins, cubrid-language-server script and uv.lock.
Keep core/CLI zero mandatory Python runtime dependencies. Preserve cubrid-lint and existing public interfaces.
You may update public README/index links consistently. Coordinate recipe/MANIFEST changes with root.
Do not edit native source, worker/profile/position code, canonical models, completion, schema.py, config.py or validation/service.py.
If a shared seam needs a fix, report the exact need to root before mutation.
Native06 expands coverage in parallel. Root will message its integration tip when available; merge it and rebuild matching native artifacts before final qualification.
Do not reuse a parent worker after its coverage revision diverges from your checkout.

## Required behavior

Use optional pygls and LSP3.17 over stdin/stdout only. No TCP/WebSocket listener, runtime download or shared daemon.
Pin the actually tested optional dependency set. Use explicit Full sync and enforce UTF-16 consistently in workspace/negotiation and core conversions.
Read preflight's framework encoding trap; plain initialize feature hooks are after framework workspace creation.
Implement initialize/initialized, open/change/close, completion, config updates, schema reload command, shutdown/exit and cancellation.
Advertise only implemented features. Analyze only documents opened with exact languageId cubrid, not generic SQL.
Use original immutable source strings and DocumentMap. Reject invalid positions, UTF-16 surrogate interiors and CRLF interiors.
Return explicit completion textEdits for whole replacement spans including token suffixes. Use complete(...) and cached schema metadata.
Use shared resolve_config, Validator and load_snapshot/refresh_snapshot; no duplicate grammar/config implementation.
Trusted editor/initialization settings select worker/runtime explicitly. Project metadata cannot select executables or credentials.
File documents use CLI filename mode defaults/config precedence. Untitled cubrid documents use SQL mode unless the client explicitly sets mode.
Support explicit snapshot clearing, stale retention and visible configured-load/refresh failures. Absent optional snapshots should still permit keywords.
Debounce diagnostics by250ms; run blocking validation/worker cleanup off the event loop. Completion remains responsive during missing/starting/slow/failing native work.
Tie async work/results to document versions; discard superseded results, cancel owned work and publish empty diagnostics on close.
Cancelling an executor future alone does not stop its thread: close the owned Validator/worker and prevent queued/late worker starts. Use the library's tested close semantics.
A cancelled request uses the protocol cancellation error. Protocol stdout contains messages only; logs/native stderr remain separate.
Missing optional dependencies print install guidance on stderr and exit3 through the installed server command.

## Tests and evidence

Exercise real framed stdio protocol, including omitted/UTF-8-first encoding offers, Unicode/CRLF edits, invalid positions, full changes, profile/mode/config precedence, optional snapshot refresh/clear/stale state and non-cubrid exclusion.
Test slow/failing worker responsiveness, stale version suppression, owned cancellation/close/shutdown and actual qualified native diagnostics.
Use explicit protocol child fixtures at trusted worker paths for deterministic delays/failures; do not add production test-delay settings.
Default tests stay independent of ignored native artifacts and optional LSP availability. Mandatory LSP/native checks must fail clearly when prerequisites are absent.
Build your checkout's own native worker from exact inputs in native README; root integration may advance its worker while you work.
Run supported Python3.10/3.14 checks, full available/native/LSP suites, isolated optional/nonoptional installs and distributions.
Record criterion evidence, commands/counts, baseline/commit, unrelated dirt and limits in docs/tickets/reports/05.md. Commit scoped work before review.
No destination merge, main merge/push, deployment, database/daemon or pinned-source/runtime mutation is authorized to the implementer.
