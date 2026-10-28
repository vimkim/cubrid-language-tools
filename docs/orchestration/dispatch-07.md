# Central ticket 07 dispatch

Baseline: `3653199a6ddd5e91982c736d576be2b481d205c0`. Branch: `central/ticket-07`.
Checkout: `/home/vimkim/gh/cubrid-language-tools-07`.
Destination: `implement/central-engine` in the coordinator checkout.

Read AGENTS.md, docs/spec.md, contracts.md, execution.md, tickets/07-schema-engineer.md,
orchestration/schema-engineer-preflight.md, report06, native AUDIT.md/QUERY_DML_AUDIT.md/README.md,
personal CUBRID policy and TDD skill. Use one fresh context for this bounded ticket.
The user gave standing approval for all planned local ticket integrations. Root performs committed review and serialized merges; do not ask permission or merge the destination yourself.
The current graph delivers the Python stage; Rust migration/formatting/consumers remain later.

## Ownership

Own native schema/engineer feature predicates and required scanner/registry/worker/build/profile adaptations, audits, qualification evidence and native tests.
You may edit validation/profiles.py and validation/worker.py for newly qualified kinds/revision while preserving public WorkerConfig/NativeWorker/ValidationResult interfaces.
Do not edit canonical models, validation/__init__.py/service.py, config.py, completion/schema, CLI, LSP, pyproject, uv.lock or root recipes/MANIFEST.
LSP05 is in a separate branch and owns optional packaging. Report any shared-seam need to root before edits.

## Required scope and safety

Qualify bounded CREATE/ALTER/DROP TABLE, VIEW, INDEX and SERIAL forms.
Qualify exact release-valid engineer forms for SHOW, DESCRIBE/DESC/EXPLAIN, EVALUATE, statistics, tracing, transaction and settings statements as ticket07 requires.
Use the source for actual spellings. EXPLAIN in this build shares the class-description production; do not assume generic EXPLAIN SELECT.
Read preflight's catalog-dependent SHOW paths. Never admit all SHOW/DESCRIBE solely because they produce PT_SELECT.
Catalog-dependent forms must be unsupported before parsing. Do not fabricate database/user/auth state or connect a DB to force offline success.
EVALUATE and SQL SET are syntax only: never evaluate expressions or apply settings/transactions. Verify qualified settings remain unchanged across subsequent requests after parsing SET/TRACE/transaction forms.

Use conservative per-family feature predicates before native calls, exact reachable-action/helper/parameter/error audits, positive/malformed/incomplete/Unicode/mixed fixtures and actual no-execution traces.
Reuse the query/DML baseline only where its reachable paths remain audited. Datatype/DDL words can also introduce expression functions; context exceptions must be deliberate and covered by negative closure cases.
Retain/reuse the reproducible reduction-candidate inventory approach, distinguishing candidates from manual context proof. Bind grammar/helper/generator/predicate hashes.
Update coverage revision, supported kinds and manifests consistently; preserve strict status/tree/diagnostic/coverage invariants, Unicode precision and owned lifecycle.
Retain regression corpus, updating formerly unsupported expectations only where a newly audited form intentionally supersedes them. Excluded features remain explicit.
If a required family cannot be safely qualified, report concrete source/runtime evidence promptly and retain an honest incomplete checkpoint rather than dropping a criterion.
Do not execute SQL, use CSQL/session/compiler/catalog lookup APIs, launch daemons/databases, alter pinned source/runtime or substitute source headers.

## Exact source and runtime

Source /home/vimkim/gh/cubrid-rust/reference-cubrid-cc947788 at cc947788d3b7dc402f46192d0f3299ddcc8563ba (read-only).
Generated /home/vimkim/gh/cb/develop/build_preset_debug_gcc.
Library /home/vimkim/gh/cb/develop/build_preset_debug_gcc/cs/libcubridcs.so.11.5.
Library SHA25656eb36e9a46e3b6f5258974b25085b81d1679430618041343e4d979704822b33.
Runtime /home/vimkim/.cub/install/develop/debug.
Follow root native recipes and build your own matching worker. Stale coverage identities must fail explicitly, never fall back.

Run full mandatory native/adapter/CLI corpus and available project tests, actual traced fixtures, wheel/sdist and isolated installation checks.
Record every criterion, exact commands/counts, baseline/commit, source/action audits, identities, unrelated dirt and limits in docs/tickets/reports/07.md.
Commit scoped implementation/report before review. No main merge/push/publication/deployment or destination writes.
