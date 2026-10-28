# 09: Distribution and final qualification

Status: complete for coordinator integration. Independent source review passed at `96d6fb5`; corrected eight-environment qualification passed at archive snapshot `4c756d6`.
Dependencies: 05, 07, 08. The coordinator confirmed the ticket 07 qualification gate on 2026-10-29.

Read [spec](../spec.md), [contracts](../contracts.md), and [execution](../execution.md).
The exact dispatch record supplies the immutable baseline and checkout.

## Scope and ownership

Own final documentation, portable fixtures, release checks and the supported coverage matrix.
Coordinate shared changes and final standards/spec review.

## Acceptance criteria

- [x] Build/install the distribution in isolated environments. Demonstrate core and CLI with no mandatory Python dependency and LSP with pinned optional dependencies.
- [x] Verify library, CLI and LSP parity for Unicode ranges, completion, coverage and failure semantics against the qualified native profile.
- [x] Publish accurate installation steps, manifest/runtime prerequisites, licensing/notices, supported coverage, known limits and consumer integration examples.
- [x] Run final standards/spec review and resolve findings with proportionate checks before final integration approval.
- [x] Update durable state and long-term roadmap. No consumer implementation or remote publication is implied.

## Report

Commit scoped changes. Record each criterion's evidence in `reports/09.md`.
Include exact commands, counts, baseline, commit, unrelated dirt, limitations, and unfinished work.
Completion requires all criteria. Request integration only after a committed result is reviewable.
