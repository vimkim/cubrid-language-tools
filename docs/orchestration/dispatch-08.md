# Central ticket 08 dispatch

Baseline: `925c90ac9dcf555dde2fee5b15357d1a4f7f088a`. Branch: `central/ticket-08`.
Checkout: `/home/vimkim/gh/cubrid-language-tools-08`.
Destination: `implement/central-engine` in the coordinator checkout.

Read AGENTS.md, docs/spec.md, contracts.md, execution.md, tickets/08-script-boundaries.md,
orchestration/script-boundaries-preflight.md, integrated reports03/05 and TDD skill.
Use one fresh context. User standing approval covers planned ticket integration; root still reviews and serializes merges. Do not ask ticket permission or merge destination yourself.
The graph now depends on03stable Validator and05LSP, not07coverage.09still waits for07explicitly.
07is a separate partial checkpoint awaiting user choice about four offline class-description forms. Do not resolve or depend on that scope choice.

## Ownership

Own shared script splitting/classification (for example cubrid_language/scripts.py), validation/service.py integration and new focused script tests.
Use canonical Span/Diagnostic/ValidationResult and existing NativeWorker. Keep CLI/LSP adapters thin and unchanged if shared Validator behavior suffices.
Add mandatory real CLI/native script tests under tests/native_parser; real LSP script cases under tests/lsp_native or tests/lsp as appropriate.
You may extend existing validator tests where new script behavior supersedes an expectation.
Do not edit C++/native/, worker.py/profiles.py/positions.py/models.py, config/schema/completion, packaging/uv.lock or root recipes/MANIFEST.
Coordinate any extra shared-file change with root before edits. Core/CLI remain zero mandatory runtime dependencies.
Publish scoped Korean/English script guides consistently; preserve accepted public docs and separate-consumer ownership.

## Behavior

Validate SQL mode as SQL. CSQL mode models files/batch text, not interactive control effects.
Read preflight: pinned source and Korean manual place lexical-block override in interactive mode; batch command detection respects strings/comments/quoted identifiers.
The manual allows leading blanks, but pinned raw batch dispatch checks line_read[0]. Do not certify unproven indented command variants; conservative unsupported is acceptable and must be documented.
Initially qualify exact full ;help, ;exit, ;autocommit on/off lines only, with documented case-insensitivity. Abbreviations, extra arguments, shell/! commands, includes, buffer controls and PL/CSQL remain unsupported.
Never invoke CSQL or SQL execution, follow includes, spawn a shell, acquire credentials, connect databases or mutate session settings.
The checker inspects the whole document; accepted commands do not actually exit or change autocommit.

Retain original source and half-open code-point spans through Unicode, CRLF, comments, quotes, semicolons and final EOF.
Prefer validating original SQL chunks with explicit local-to-document diagnostic translations. Do not normalize/mutate original text or guess token precision.
Unqualified procedural blocks must remain opaque rather than turning inner semicolons into successful standalone SQL checks; document conservative recovery limits.
Retain both syntax and unsupported diagnostics and priority tool>syntax>unsupported>valid. A later failure must not erase earlier findings or become a partial pass.
A script containing only approved commands, empty content or unsupported regions still observes input/profile/worker availability requirements before any complete pass.
Preserve all existing input limits, native-error guards, owned cancellation/close behavior and explicit coverage semantics.

## Tests and qualification

Use public classify/Validator/CLI/LSP seams. Cover EOF without final semicolon, quoted/comment semicolons, multiline lexical blocks, doubled/backslash escapes, Unicode+CRLF offsets, adjacent SQL/commands, malformed/incomplete tokens, mixed syntax/unsupported/tool errors and unknown/missing profiles/workers.
Prove includes/shell text causes no referenced-file reads/marker writes or execution.
Keep default tests independent of ignored native artifacts/optional LSP packages. Actual native and optional LSP script qualification must be explicit mandatory checks.
Own native baseline isV2, build using native README exact pinned inputs;07mayadvance profile/private observations but public WorkerConfig/NativeWorker/Validator interfaces remain unchanged.
If07is integrated before your final checks, merge current integration and rebuild matching worker. Do not treat stale coverage as a pass.
Run full available/default, native/CLI, optional framed/native LSP and distribution/isolated install checks on supported Python3.10/3.14 as relevant.
Record each criterion, command/count, baseline/commit, original spans, unrelated dirt and limits in docs/tickets/reports/08.md.
Commit scoped source/report before review. No destination/main merge, push, deployment, DB/daemon or pinned-source/runtime mutations.
