# Central engine final review

Status: both source review axes pass at `96d6fb5e85ce656f9fd1516ba1ce4a3922d02c44`.
Fresh native qualification and corrected installed-artifact checks remain pending.
Final main integration remains gated on those results and its separate approval.

## Review baseline

- Fixed point: accepted main `721b9bca96d91951ea81f95be755a9e30ca5a20b`.
- Initial candidate: `c7f6c4d9ba096989ecfb2ce55eee59faceb884cc`.
- Comparison: `git diff 721b9bca96d91951ea81f95be755a9e30ca5a20b...c7f6c4d9ba096989ecfb2ce55eee59faceb884cc`.
- Standards: [AGENTS.md](../../AGENTS.md), [execution](../execution.md), [contracts](../contracts.md), and the personal CUBRID policy.
- Specification: [spec](../spec.md), [contracts](../contracts.md), the revised [ticket graph](../tickets/README.md), and dispatch records.

Two independent agents reviewed the same committed changes. Their findings remain separate below.
Verification was read-only and included pure completion reproductions and source inspection.
Existing test evidence was considered. Reviewers did not repeat native or installation suites.
The user-approved description exclusions were accepted scope, not missing requirements.

## Standards

### Documented violations

- **P2: completion lexical suppression.** The inherited lexer omits `//` comments and backslash-escaped quotes.
  Public calls return suggestions inside those contents, contrary to the completion contract.
  Correct the pure lexer and add public and framed LSP regressions.
- **P2: diagnostic truncation loses earlier findings.** The native worker throws after collecting diagnostics at the cap.
  Its outer handler returns only a tool failure and discards the earlier syntax and unsupported findings.
  Preserve a bounded diagnostic prefix and an explicit truncation error.

### Judgment call

- **P3: kind depends on display detail.** `CompletionItem.kind` derives its value from descriptive text.
  Empty detail or the lone word `catalog` can raise `IndexError`.
  A defensive fallback can preserve compatibility. An explicit-kind redesign is not required for this delivery.

Standards result: two P2 violations and one P3 judgment call. The worst severity is P2.

## Specification

- **P2: completion leaks into comments and escaped strings.** The contract requires suppression within comments and strings.
  Both `// SEL` and an unfinished string containing a backslash-escaped quote produce SQL candidates.
- **P2: mixed CSQL completion loses document context.** Session mode is selected from the whole document prefix.
  `;help` followed by an unfinished SQL line returns no SQL candidates.
  A session command after earlier SQL returns no command candidates.
  Select the active SQL or command context and preserve original document offsets.

No additional confirmed scope, status, Unicode-range, lifecycle, configuration-trust, or release-harness findings were reported.
Specification result: two P2 findings. The worst severity is P2.

## Coordinator finding

The bilingual coverage guides initially described status priority as the reverse of their displayed list.
That wording incorrectly placed unsupported results above syntax errors.
Commit `a32b4d2de9309123e346f164538cc4a8d6fb1fad` states the explicit contract order in both languages:
`tool-error > syntax-error > unsupported > valid`.
Markdown and diff checks passed. Artifact refresh remains part of final qualification.

## Resolution and verification

Both reviewers inspected the committed fixes through `96d6fb5e85ce656f9fd1516ba1ce4a3922d02c44`.
They reported no remaining actionable violation in either axis.
Ticket 09 owns these fixes and their public regression tests.

The standards reviewer closed lexical suppression and diagnostic preservation.
The defensive kind fallback resolves the crash while preserving the public constructor.
Deriving kind from detail remains a nonblocking design heuristic.

The specification reviewer closed lexical suppression and mixed-document completion.
SQL delimiters with whitespace or trailing comments retain scope.
Active semicolon command completion, multiline lexical protection, and original Unicode/CRLF ranges remain intact.

Follow-up regressions also cover empty malformed diagnostic lists and valid empty-statement gaps.
Ordinary source-trivia checks reject omitted nontrivial text.
Truncation preserves marker, count, type, status, coverage, observation, and statement-kind checks.
Exactly 256 ordinary findings fit. A 257th produces a retained prefix and explicit T1002.

Source review result: zero open actionable standards findings and zero open specification findings.
Native and installed-artifact qualification are separate gates. Their pending state is not a source review pass.

The original 230 completion observations remain historical parity evidence.
Changed native source requires a new worker, manifest, corpus replay, and trace evidence.
The earlier eight-environment installation pass remains historical evidence for its original source snapshot.
The final [ticket report](../tickets/reports/09.md) must identify the corrected artifacts and follow-up review results.
