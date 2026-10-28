# 05: Shared LSP adapter

Status: specified. Dependencies: 03, 04.

Read [spec](../spec.md), [contracts](../contracts.md), and [execution](../execution.md).
The exact dispatch record supplies the immutable baseline and checkout.

## Scope and ownership

Own optional pygls LSP adapter, dependency pins, server entry point and protocol tests.
Coordinate packaging/recipe edits. Editor products remain outside this repository.

## Acceptance criteria

- [ ] Implement stdio LSP 3.17 lifecycle, full sync, UTF-16 completion textEdits and versioned diagnostics for cubrid documents.
- [ ] Use the same core/config/snapshot interfaces as CLI. Support configuration changes and explicit snapshot reload.
- [ ] Debounce native checks, keep event loop responsive, cancel owned pending work, discard stale versions and clear close diagnostics.
- [ ] Completion works with absent runtime. Unknown encodings/positions and cancellation follow protocol behavior.
- [ ] Protocol stdout contains only messages. Missing optional dependencies print install guidance and exit with tool failure.
- [ ] Run headless protocol tests with real adapter and qualified worker, then distribution checks.

## Report

Commit scoped changes. Record each criterion's evidence in `reports/05.md`.
Include exact commands, counts, baseline, commit, unrelated dirt, limitations, and unfinished work.
Completion requires all criteria. Request integration only after a committed result is reviewable.
