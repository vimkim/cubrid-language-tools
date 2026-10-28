# 04: Offline schema snapshots

Status: specified. Dependencies: 01.

Read [spec](../spec.md), [contracts](../contracts.md), and [execution](../execution.md).
The exact dispatch record supplies the immutable baseline and checkout.

## Scope and ownership

Own JSON schema loading/refresh and tests. Core completion still performs no I/O.

## Acceptance criteria

- [ ] Implement schemaVersion 1 with required typed fields and optional users/database/system/indexes retained.
- [ ] Reject invalid required fields, preserve spelling, ignore unknown fields and perform no database/credential access.
- [ ] Initial failure yields no schema with an availability message. Failed refresh retains last valid schema with explicit stale state.
- [ ] Test public loading/refresh and completion behavior with absent, valid, invalid and changed snapshots.

## Report

Commit scoped changes. Record each criterion's evidence in `reports/04.md`.
Include exact commands, counts, baseline, commit, unrelated dirt, limitations, and unfinished work.
Completion requires all criteria. Request integration only after a committed result is reviewable.
