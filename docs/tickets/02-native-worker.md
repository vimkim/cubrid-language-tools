# 02: Qualified native worker

Status: specified. Dependencies: none.

Read [spec](../spec.md), [contracts](../contracts.md), and [execution](../execution.md).
The exact dispatch record supplies the immutable baseline and checkout.

## Scope and ownership

Port the incomplete native checkpoint into this package and finish its missing qualification.
Own `native/parser-worker/`, `src/cubrid_language/validation/`, native tests and `test_validation_*.py`.
Import Span from cubrid_language.models. Do not edit shared models, packaging, recipes, or completion files.
Use existing recipe interfaces. Request coordinator changes if necessary.
Reuse the clean pinned source and exact runtime read-only. Do not modify CUBRID source or initialize a database.

## Acceptance criteria

- [ ] Bind exact source, generated headers, library hash, runtime assets, profile settings, platform, and coverage revision in build and runtime manifests.
- [ ] Qualify literal SELECT and CREATE SERIAL with valid, malformed, incomplete, empty, multiple, Korean/emoji/CRLF inputs over JSON lines.
- [ ] Apply conservative feature predicates before native parsing. Reject tables, CTEs, subqueries, functions, arithmetic, hints, and unknown forms outside the admitted subset.
- [ ] Write a full reachable-action audit for admitted productions, initialization, helper calls, syntax parameters and excluded catalog/execution paths, with pinned-source lines.
- [ ] Handle ordinary parser errors, partial trees, internal-error flags, mismatched profile/library/manifest, missing assets, malformed replies, deadlines, crashes, cancellation and size limits without a pass.
- [ ] Add a deterministic induced internal-error test at the native classification interface, confined to a test build and absent from the production request protocol.
- [ ] Preserve Unicode/UTF-8/UTF-16 mapping correctness and bounded memory. Use statement spans when native coordinates are unreliable.
- [ ] Validate response invariants including diagnostic categories, ranges, status/coverage consistency and manifest identity. Serialize native requests off the event loop and reap only the owned worker.
- [ ] Trace representative actual native parsing with no network, database connection, descendant client or external writable configuration. Retain corpus-specific evidence and limits.
- [ ] Complete notices and runtime/build/install instructions. Run mandatory native tests, independent worker/position tests, the available project suite, and Python distribution build. Missing prerequisites must fail visibly.

## Report

Commit scoped changes. Record each criterion's evidence in `reports/02.md`.
Include exact commands, counts, baseline, commit, unrelated dirt, limitations, and unfinished work.
Completion requires all criteria. Request integration only after a committed result is reviewable.
