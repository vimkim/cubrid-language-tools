# 07: Schema and engineer coverage

Status: specified. Dependencies: 06.

Read [spec](../spec.md), [contracts](../contracts.md), and [execution](../execution.md).
The exact dispatch record supplies the immutable baseline and checkout.

## Scope and ownership

Own DDL and engineer-statement coverage families, source audits, manifests and fixtures.

## Acceptance criteria

- [ ] Qualify CREATE/ALTER/DROP TABLE, VIEW, INDEX and SERIAL within documented safe subsets.
- [ ] Qualify documented offline subsets of SHOW, EVALUATE, statistics, tracing, transaction and settings forms. Keep SHOW COLUMNS, DESCRIBE, DESC and class-description EXPLAIN explicitly unsupported.
- [ ] Use pinned source for actual spellings. Unsupported kinds/features remain explicit and cannot enter unaudited native actions.
- [ ] Retain full action/settings audits, positive/negative/mixed fixtures, original ranges and no-execution traces.
- [ ] Run native and shared adapter regression corpus and publish exact limits.

## Accepted first-profile limit

The user accepted this limit on 2026-10-29 after reviewing the native connection-guard evidence.
SHOW COLUMNS, DESCRIBE, DESC and class-description EXPLAIN remain unsupported before native parsing.
Their pinned client helpers report ER_OBJ_NO_CONNECT (-224) even when a parser tree exists.
A separately qualified parser-only backend is a follow-up. Do not connect a database or simulate connection state.
This scope revision replaces the original describe-family qualification criterion.

## Report

Commit scoped changes. Record each criterion's evidence in `reports/07.md`.
Include exact commands, counts, baseline, commit, unrelated dirt, limitations, and unfinished work.
Completion requires all criteria. Request integration only after a committed result is reviewable.
