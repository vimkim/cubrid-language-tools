# 03: Shared validation and lint CLI

Status: specified. Dependencies: 01, 02.

Read [spec](../spec.md), [contracts](../contracts.md), and [execution](../execution.md).
The exact dispatch record supplies the immutable baseline and checkout.

## Scope and ownership

Own document validation, trusted configuration, CLI adapters, CLI entry point, and their tests.
Use native results and canonical models. Keep language decisions out of output formatting.

## Acceptance criteria

- [ ] Implement validate(text,profile,script_mode) with explicit configured worker ownership and contract result aggregation.
- [ ] Implement cubrid-lint paths/stdin, human/JSON output, code-point spans, per-file results, default modes and the exact 0/1/2/3 exit priorities.
- [ ] Reject invalid UTF-8, NUL, invalid flags/config, duplicate stdin and unavailable input through explicit tool results. Malformed args exit 3.
- [ ] Discover project config with documented precedence. Only trusted settings or explicit flags can select worker executable/runtime.
- [ ] Cover mixed valid/syntax/unsupported/tool files, unknown profiles, empty files and unavailable workers through the actual command entry point.
- [ ] Run focused CLI tests, available project suite and package build.

## Report

Commit scoped changes. Record each criterion's evidence in `reports/03.md`.
Include exact commands, counts, baseline, commit, unrelated dirt, limitations, and unfinished work.
Completion requires all criteria. Request integration only after a committed result is reviewable.
