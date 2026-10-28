# 01: Independent completion library

Status: specified. Dependencies: none.

Read [spec](../spec.md), [contracts](../contracts.md), and [execution](../execution.md).
The exact dispatch record supplies the immutable baseline and checkout.

## Scope and ownership

Port the pure completion checkpoint into `cubrid_language` without terminal or csql-future imports.
Own `src/cubrid_language/{__init__,models,completion,syntax,completion_data}.py`, completion tests, and completion provenance notes.
Preserve the shared Span implementation and extend models with immutable completion/schema values.
Keep the checkpoint algorithm and vocabulary provenance. Remove terminal-menu and legacy compatibility concerns from central tests.

## Acceptance criteria

- [ ] An editable install imports cubrid_language with no csql_future module installed and no mandatory runtime dependency.
- [ ] Public complete(text,cursor,profile,schema=None) returns immutable deterministic items and the shared Span. Validate cursor types and bounds.
- [ ] Preserve expanded session commands, parameter values, users/database/system/index metadata, owner shadowing, quoted names, aliases, suffix replacement, comments and string suppression.
- [ ] Korean, emoji, multiline and CRLF fixtures replace the correct original token.
- [ ] Completion performs no filesystem, environment, network, subprocess or terminal operations.
- [ ] Port the relevant checkpoint completion corpus through the public interface. Prove parity with original suggestion values and range behavior.
- [ ] Run just test-language-core, just test and just build. Record vocabulary provenance and strict-parser profile differences.

## Report

Commit scoped changes. Record each criterion's evidence in `reports/01.md`.
Include exact commands, counts, baseline, commit, unrelated dirt, limitations, and unfinished work.
Completion requires all criteria. Request integration only after a committed result is reviewable.
