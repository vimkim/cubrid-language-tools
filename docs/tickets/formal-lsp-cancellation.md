# Formal verification: LSP bulk cancellation

Follow-up to the completed central engine, work item 572. Tracked separately as work item 579.

## Property and harm

Bulk cancellation must gate every queued validation job in the batch before cleanup of an active worker can free a validation thread.
Otherwise configuration changes or shutdown can start a worker for a document whose validation is being cancelled.

Ground this property in `Adapter.stop_jobs`, `Adapter.stop_job`, and `ValidationJob.run` in `src/cubrid_language/lsp_server.py`, together with the configuration and shutdown callers.
Compare worker ownership with `Validator.close`/`validate` and `NativeWorker.close`/`_start`; keep any additional claims within the evidence.

## Ownership

Create a discoverable project-local skill under `.agents/skills/verify-lsp-cancellation/` and the executable verification resources it needs.
Write acceptance evidence in `docs/tickets/reports/formal-lsp-cancellation.md`.
Product code must remain unchanged. Findings must remain findings.
Shared `justfile`, packaging, dependency and historical orchestration edits belong to the coordinator; request those by message if needed.
Prefer a directly runnable command requiring no recipe change and no mandatory runtime dependency.

## Acceptance

1. Compare this target with nearby stale-diagnostic and worker-lifecycle promises, and explain the selection.
2. Choose the least costly tool that checks the event-ordering property exhaustively in a stated finite scope. TLA+/TLC is the default for this ordering question; pin and verify any downloaded tool. A different tool needs an evidence-backed reason.
3. Map each modeled action and atomicity boundary to the actual Python code, including the independent cleanup and validation executors. Do not collapse cancellable thread interleavings into an atomic batch merely because the event-loop handler has no await.
4. Explore the full configured scope, report states/interleavings, and distinguish absence of counterexamples from liveness or unbounded claims. Keep reruns cheap.
5. Demonstrate each claimed property failing on a scratch real-code mutation. A source-drift/hash refusal alone does not count: replay a reachable violating schedule against the mutated implementation. Restore product code and rerun.
6. Write the local skill for a cold agent: trigger/frontmatter, one rerun command, tool/bootstrap details, source/function coverage, full sync commit, bounds/assumptions, result interpretation, and maintenance instructions. Advance the sync commit only after checking source/model correspondence.
7. For TLA+ results, invoke `/statechart` for interpretation and leave that requirement in the generated skill. Refer to the skill by name; do not embed its installation paths or commands in generated resources.
8. Follow the generated skill end to end, record the observed mutation failure and restored baseline, validate skill frontmatter, run proportionate existing LSP checks, review the diff, and commit task changes.

Record exact commands, baseline, tool versions, counts, findings, limitations, unrelated dirt, and artifact paths in the report.
Do not fix product bugs, integrate, push, or publish as part of this ticket.
