# Central engine final review

Status: both source review axes pass at `96d6fb5e85ce656f9fd1516ba1ce4a3922d02c44`.
Fresh native qualification and corrected installed-artifact checks pass.
Final main integration requires its separate approval. See the [delivery report](../tickets/reports/09.md).

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

Initial standards result: two P2 violations and one P3 judgment call. The worst severity is P2.

## Specification

- **P2: completion leaks into comments and escaped strings.** The contract requires suppression within comments and strings.
  Both `// SEL` and an unfinished string containing a backslash-escaped quote produce SQL candidates.
- **P2: mixed CSQL completion loses document context.** Session mode is selected from the whole document prefix.
  `;help` followed by an unfinished SQL line returns no SQL candidates.
  A session command after earlier SQL returns no command candidates.
  Select the active SQL or command context and preserve original document offsets.

No additional confirmed scope, status, Unicode-range, lifecycle, configuration-trust, or release-harness findings were reported.
Initial specification result: two P2 findings. The worst severity is P2.

## Coordinator finding

The bilingual coverage guides initially described status priority as the reverse of their displayed list.
That wording incorrectly placed unsupported results above syntax errors.
Commit `a32b4d2de9309123e346f164538cc4a8d6fb1fad` states the explicit contract order in both languages:
`tool-error > syntax-error > unsupported > valid`.
Markdown, diff, and final archive checks pass. The corrected coverage text is included in qualified snapshot `4c756d6`.

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
Native and installed-artifact qualification are separate gates. Both now pass.

The original 230 completion observations remain historical parity evidence.
The corrected native source has a fresh worker/manifest, a successful 325-case corpus replay, and renewed no-execution trace evidence.
The earlier eight-environment installation pass remains historical evidence for its original source snapshot.
The corrected installed snapshot is `4c756d6925a3850d49fbeb4ed692860ba6d99ef0`, with unchanged reviewed engine `96d6fb5`.
All eight Python 3.10.6/3.14.0 wheel/source core/optional installs pass. Each core environment passes 109 defaults and public parity.
Each optional environment passes 28 framed tests and public parity. Every variant checks 11 validation and six completion cases.
Fresh native checks pass 45 native/CLI, 20 independent, and six actual-native LSP tests.
The 325-case trace records one worker exec and no descendants, network calls, or external writable opens.

- Current manifest: `34b4b020ef6858c9aa0707de8617d67dfd8336f1a67220b600988e2935893dee`.
- Current worker: `9af56541bc0d90dc63ce11ae0af2122c2dfa31720e92f38992656909d5e26548`.
- Current trace: `5611f9bbb496e38c49f5e7aa712fa86b0f8a33bffc86bd1a854cf34941fdc422`.

The final [ticket report](../tickets/reports/09.md) records exact commands, artifact hashes, remaining limits, and preserved evidence.
Later prose/metadata commits preserve the reviewed engine and receive fresh archive byte checks. Main approval remains a separate internal integration gate.
