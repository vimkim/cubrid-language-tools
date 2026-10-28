# 06: Query and DML coverage

Status: specified. Dependencies: 02.

Read [spec](../spec.md), [contracts](../contracts.md), and [execution](../execution.md).
The exact dispatch record supplies the immutable baseline and checkout.

## Scope and ownership

Own separate native coverage families, audits and fixtures for queries and DML.
The central completion interface remains unchanged.

## Acceptance criteria

- [ ] Qualify SELECT, joins, expressions, CTEs/subqueries, INSERT, UPDATE, DELETE and MERGE using pinned-source grammar evidence.
- [ ] Conservative predicates precede native calls and handle quoted/commented tokens without accidental broad admission.
- [ ] Retain positive/negative/incomplete Unicode fixtures and classify catalog-dependent or internal failures explicitly.
- [ ] Record full reachable grammar/action/settings audit and traced no-execution evidence for every newly admitted family.
- [ ] Publish exact qualified limits and run the mandatory native/adapter corpus.

## Report

Commit scoped changes. Record each criterion's evidence in `reports/06.md`.
Include exact commands, counts, baseline, commit, unrelated dirt, limitations, and unfinished work.
Completion requires all criteria. Request integration only after a committed result is reviewable.
