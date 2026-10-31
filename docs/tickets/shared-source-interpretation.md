# Shared source interpretation

Work item 649 follows the completed architecture review, work item 648.
The user confirmed the narrow ownership design on 2026-10-31.
The product baseline is `3b9d5af67e530423aa6a9e435b06cb8d629c9e5b`.
The coordinator supplies the exact dispatch commit after committing this ticket.

## Goal and contract

Make completion and authoring easier to change and test without changing their public results.
Read `AGENTS.md`, `GLOSSARY.md`, `docs/spec.md`, `docs/contracts.md`, `docs/architecture.en.md`, and `docs/tickets/show-hint-design.md` first.
The [completion provenance](../completion-provenance.md) and [hint repair report](reports/show-hint-authoring.md) explain behavior that this refactor must preserve.

The worktree is `/home/vimkim/gh/cubrid-language-tools-source-interpretation`, on `refactor/shared-source-interpretation`.
Its integration destination is `main` in `/home/vimkim/gh/cubrid-language-tools`.
Local task commits are authorized.
The coordinator owns the ticket, glossary, acceptance report, work ledger, and integration review.
The implementer owns only the three production modules below and focused public characterization tests.
Do not rebase, merge, push, install globally, or modify other worktrees.

## Accepted shape

Add private `cubrid_language._source` as the owner of the existing tolerant `Token`, `unquote`, and `tokenize` behavior.
It also owns `AuthoringPart` and `authoring_parts(text)`.
An immutable authoring part pairs an original-document `Span` with a tuple of tokens relative to that span's start.
Its tokens must equal tokenizing that exact source slice, including order, offsets, depth, spelling, kind, and closure flags.

`authoring_parts` uses the unchanged `scripts.classify` result and the existing conservative trigger-prefix rule.
Scan each classified SQL part once, retain comments, locate the first trigger header, and retain only the eligible prefix and its tokens.
Keep an eligible part even when it contains no tokens.
Do not reuse completion's global token stream for region-local authoring.

Completion keeps its existing whole-document, session-argument, and hint-argument interpretations.
It reads hint eligibility from the shared authoring parts.
Authoring iterates those parts and their retained tokens instead of tokenizing the same eligible slice again.
Move both callers and delete the old tokenizer definitions, `sql_parts`, and their lazy imports in one change.
Do not leave forwarding aliases or two implementations.
Existing hint inventory imports can remain one-way; moving inventory or completion context selection is outside this ticket.

## Preserve

- Keep `complete` and `authoring_diagnostics`, package exports, public result values, validation order, and exception types unchanged.
- Preserve ordered candidates, full-token replacement, allowed and availability values, exact diagnostic order, and warning-only semantics.
- Preserve original Unicode code-point offsets, CRLF, Korean, emoji, quote styles, incomplete input, token-left-edge edits, and scanner-specific escaping.
- Preserve both authoring script modes using the current eligibility policy and the exact-profile early return before scanning.
- Preserve CSQL command recovery, conservative trigger-tail suppression, and the difference between global and region-local lexical origins.
- Leave `scripts.py`, native worker checks, validation aggregation, LSP job lifecycle, configuration, acquisition, packaging, recipes, and dependencies unchanged.
- Add no I/O, cache, parser replacement, generic adapter, or new public interface.

For example, `;read 'unclosed` followed by a newline and `SELECT /*+ BOGUS */ 1;` produces an authoring warning even though completion's global tokenizer consumes the later text as an unfinished string.
A universal token stream would change this behavior.
The classifier also treats `BEGIN$` differently from completion's tokenizer; preserve its current suppression.

## Verification and delivery

Before moving production code, add focused public characterization cases for the malformed-command lexical origin, trigger-prefix boundaries, and relevant input/profile behavior not already covered.
Run them against baseline production and commit that behavior pin first.
This is a behavior-preserving refactor, so the pin is expected to pass before and after.
Do not add tests that merely assert helper locations, scanner call counts, or private intermediate lists.

The coordinator has frozen 163 baseline inputs with 1,341 completion and 326 authoring observations at:

`/mnt/nvme/data-5/tmp/architecture-review-20261031T060336Z/candidate-01-design/baseline-corpus.json`

Its SHA-256 is `2226eed01ef1b821e3150bd8865d1510a5b0f3a080b267a6082a5a7470e1c716`.
Do not overwrite it or use the baseline-capture script as a candidate comparison.
The coordinator will replay these public observations against the task source and separately cover unsupported profiles and invalid public inputs.
The preliminary 159 token-prefix comparisons are finite evidence, not a proof for every input.
If a counterexample prevents faithful token retention, report it and preserve behavior rather than changing the contract.

Run the focused public tests, the existing core suite, and real framed LSP protocol tests with task-source import provenance.
The coordinator will independently inspect the diff, replay the corpus, and verify a locally installed wheel.
Report exact commits, commands, import provenance, results, and limitations.
Review the diff, stage only owned files, and commit the final implementation.
The coordinator requests main integration only after concrete acceptance evidence and the committed report are ready.
