# 07: Schema and engineer coverage

Status: specified. Dependencies: 06.

Read [spec](../spec.md), [contracts](../contracts.md), and [execution](../execution.md).
The exact dispatch record supplies the immutable baseline and checkout.

## Scope and ownership

Own DDL and engineer-statement coverage families, source audits, manifests and fixtures.

## Acceptance criteria

- [ ] Qualify CREATE/ALTER/DROP TABLE, VIEW, INDEX and SERIAL within documented safe subsets.
- [ ] Qualify release-valid SHOW, DESCRIBE/DESC, EXPLAIN, EVALUATE, statistics, tracing, transaction and settings forms.
- [ ] Use pinned source for actual spellings. Unsupported kinds/features remain explicit and cannot enter unaudited native actions.
- [ ] Retain full action/settings audits, positive/negative/mixed fixtures, original ranges and no-execution traces.
- [ ] Run native and shared adapter regression corpus and publish exact limits.

## Report

Commit scoped changes. Record each criterion's evidence in `reports/07.md`.
Include exact commands, counts, baseline, commit, unrelated dirt, limitations, and unfinished work.
Completion requires all criteria. Request integration only after a committed result is reviewable.
