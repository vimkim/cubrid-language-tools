# Implement SHOW and optimizer-hint authoring

## Dispatch

Work item 606. Product baseline is `1829fb6730663d427aaa5c4fad0574838e392349`. The coordinator supplies this ticket's exact dispatch commit in the implementer prompt. Worktree is `/home/vimkim/gh/cubrid-language-tools-show-hints`, branch `feat/show-hint-intelligence`. Destination is local `main` in the primary engine checkout.

Read AGENTS.md, docs/spec.md, docs/contracts.md, docs/coverage.en.md, this ticket, and show-hint-design.md before implementation. The user's current authorization permits shared-engine edits. Native CUBRID sources, libraries, worker build outputs, and runtime assets remain read-only.

## Acceptance

1. Commit focused failing public regressions before editing production code. Cover hint completion and an exact unknown-name warning alongside retained native unsupported/tool diagnostics. Save the actual failing commands and results.
2. Package one qualified language inventory for `cubrid-11.5.0.2704-cc94778`. Reproducibly compare every hint spelling and alias against pinned `src/parser/csql_grammar.y` at source commit `cc947788d3b7dc402f46192d0f3299ddcc8563ba`. Audit every SHOW grammar head before emitting closed-world unknown SHOW warnings. Keep all argument/placement checks tied to source evidence. Preserve existing non-hint completion provenance and behavior.
3. Complete hint names in `/*+`, `--+`, and `//+` contexts, including unfinished input, multiple hints, case variants, and cursor-middle replacement. Reuse document aliases and optional schema names for audited argument suggestions. Ordinary strings/comments and opaque procedural regions do not gain hint suggestions.
4. Expose pure authoring diagnostics and integrate them through the existing Validator entry point. Emit distinct stable A codes for completed unknown hints, audited malformed arguments or placement, and completed unknown/malformed SHOW forms. Use warning severity and category authoring. Keep native status, coverage, original text, and CLI exits unchanged except visible total-diagnostic overflow. Safely computed findings remain useful with missing native runtime. Unknown profiles and ambiguous unfinished input get no guessed closed-world findings.
5. Test suppression in ordinary comments/quoted text, mixed statements, CSQL opaque regions and procedural bodies; preserve original Unicode and CRLF spans. Correct inputs are counterexamples for each enabled lint rule. Bound the combined diagnostic output without hiding native failure context. Exercise the smallest supported diagnostic limit.
6. Verify CLI and real framed LSP expose the same warnings. Test UTF-16 positions, native unsupported coexistence, no-runtime findings, superseded document updates, correction clearing, and close clearing. Advertise useful completion triggers only when backed by implemented contexts.
7. Run the existing core, LSP, native adapter, and actual-native LSP checks with the existing qualified artifacts. A task-owned `.venv` is prepared. `native/parser-worker/build` is an ignored symlink to read-only qualified artifacts. Run the inventory verifier against the pinned source and demonstrate it catches a deliberately mismatched catalog in disposable input.
8. Update contracts, coverage/provenance and practical docs to state warning semantics and exact limits. Write actual acceptance commands, results, versions and limitations in docs/tickets/reports/show-hint-authoring.md. Commit all meaningful task changes after rereading the diff. Stage only task files.

## Ownership and evidence

Own engine product code, focused tests, relevant engine docs and the ticket report. The coordinator owns the dispatch/design documents and canonical decision log. Keep source/native qualification inputs, packaging dependencies and real user configuration unchanged. Existing tests establish 109 baseline core tests and a passing Neovim baseline; do not weaken those contracts to match new code.

Pinned native source is `/home/vimkim/gh/cubrid-rust/reference-cubrid-cc947788`. Native runtime prefix comes from the existing worker manifest. Historical SHOW helper exclusions remain in native/parser-worker/SCHEMA_ENGINEER_AUDIT.md. The recorded pre-change probe is `/home/vimkim/temp/cubrid-show-hints-606-yszqo6t9/evidence/baseline-result.json`.

Use one fresh implementation owner for this bounded ticket. Return committed tip, red/green evidence, exact verification commands and remaining limitations. Local commits are authorized. The coordinator handles review and cross-repository verification. Integration, push, publication and changes to real editor settings require their separate authorization.
