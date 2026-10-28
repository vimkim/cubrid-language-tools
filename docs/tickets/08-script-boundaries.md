# 08: CSQL script classification

Status: specified. Dependencies: 03, 07.

Read [spec](../spec.md), [contracts](../contracts.md), and [execution](../execution.md).
The exact dispatch record supplies the immutable baseline and checkout.

## Scope and ownership

Own shared script splitting/classification and mixed-document tests used by CLI and LSP.

## Acceptance criteria

- [ ] Preserve original offsets across SQL, comments, strings, quoted identifiers and CRLF when splitting statements.
- [ ] Admit only audited ;help, ;exit, ;autocommit on/off session lines initially. Includes, shell commands and PL/CSQL remain unsupported.
- [ ] Never execute commands or includes. Preserve both syntax and unsupported diagnostics with contract priority.
- [ ] Cover EOF without semicolon, quoted semicolons, incomplete tokens and mixed scripts through library/CLI/LSP.

## Report

Commit scoped changes. Record each criterion's evidence in `reports/08.md`.
Include exact commands, counts, baseline, commit, unrelated dirt, limitations, and unfinished work.
Completion requires all criteria. Request integration only after a committed result is reviewable.
