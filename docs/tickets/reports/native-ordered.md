# Native ORDERED ticket report

Editor users need safely qualified native checks for one optimizer hint.
This ticket qualifies a single argument-free block ORDERED immediately after a top-level literal SELECT.
The ticket owner result is PASS for that bounded scope. Independent root review and main integration remain pending.

## Source and artifact identity

| Item | Exact value |
| --- | --- |
| Dispatch baseline | `49479b2d0a6cf39f71498834215346d8381b82c5` |
| Tested implementation commit | `27f29a45aa4de28fdd20ea4b5b326b666d2bb8bc` |
| Tested implementation tree | `a22fcaccad94b54ccbaca57166fb5b4722bbf142` |
| Checkout | `/home/vimkim/gh/cubrid-language-tools-native-ordered` |
| Branch | `followup/native-ordered` |
| Destination | `main`, unchanged by this ticket |
| Profile | `cubrid-11.5.0.2704-cc94778` on Linux x86-64 |
| Coverage revision | `bounded-query-dml-schema-engineer-ordered-v4` |
| CUBRID source | `cc947788d3b7dc402f46192d0f3299ddcc8563ba` |
| Native library SHA-256 | `56eb36e9a46e3b6f5258974b25085b81d1679430618041343e4d979704822b33` |
| Final worker SHA-256 | `c2b89a8f7d539934f0b68cf2af66199d3889baa541859d30809cca9c91ccabd3` |
| Final manifest SHA-256 | `c93879150d6ecb4a62414876f097b029e2bec06725292bbe6673133c46bb7efc` |
| Final build evidence SHA-256 | `a66be45e7f88992afddbe3d6bc5602ffda4ec22b0ab6153adf6254090a6fab4b` |
| Final trace SHA-256 | `1045cdf1803771b7e5a72a469701b708aee9f1e97b7d875692a64d3286703529` |

The evidence directory is `/home/vimkim/temp/cubrid-followup-execution-6_7fcyif/native`.
The final same-host artifact copy is `qualified-build` under that directory.
It retains the worker, embedded-digest manifest, and build evidence after the task worktree is removed.
`copied-worker-check.json` records a real Validator sequence of valid, syntax-error, and valid through that copied worker.
It also records CUBRID-U1001 from the preserved v3 worker under the new Python identity.
That rejection is expected. Existing trusted native installs must be rebuilt or replaced with a matched v4 pair before selecting the new core.

## Scope and design

The [source audit](../../../native/parser-worker/ORDERED_HINT_AUDIT.md) follows the block lexer state, hint lookup, no-argument helper branch, SELECT action, recovery, cleanup, and settings.
The admitted native hint action only sets PT_HINT_ORDERED on the SELECT tree.
The worker keeps its existing parser lifecycle and never calls a session, optimizer, execution entry point, or database connection.

The scanner records closed block hints as raw tokens with original offsets.
The registry routes every hinted statement only to the literal SELECT predicate.
The hint can neither disappear as an ordinary comment nor fall through to a broader query or schema family.
Only space, tab, CR, and LF can separate SELECT from the hint or surround the ASCII case-insensitive name.
The original SQL bytes are sent to the parser unchanged.

Closed malformed hints, hint arguments, duplicate names or blocks, nested comments, line hints, other placements, and nonliteral SELECT bodies remain unsupported.
Unterminated comments and quoted tokens retain scanner syntax errors without native calls.
Generic SHOW, procedural syntax, other hints, and the four accepted description exclusions retain their prior limits.
There are no public interface changes or new runtime dependencies.

Two independent read-only sketches compared raw hint tokens with separate occurrence metadata.
The token design kept one existing ordered representation. The metadata design supplied the stricter whitespace-only gap.
The local `design-synthesis.md` records the comparison. The configured models did not provide a different-family arena judge.
Root owns independent review and the no-comments review.

Model the Domain kept hint placement and duplication in the existing token sequence.
Laziness Protocol limited production behavior changes to three coverage headers.
Test Behavior, Not Implementation kept tests at worker, Validator, CLI, and LSP interfaces.
Prove It Works required a real worker trace and copied-artifact checks.
Separate Before Serializing Shared State kept all native output in this ticket's worktree and evidence directory.

## Failing baseline and passing checks

The exact baseline worker was built with the four preserved README inputs before admission code changed.
It is retained in `baseline-build`, with manifest SHA-256 `34b4b020ef6858c9aa0707de8617d67dfd8336f1a67220b600988e2935893dee`.

- `tdd-baseline.log` records the worker and public Validator tests failing because the intended admitted forms returned unsupported.
- `tdd-cli-baseline.json` records CLI exit 2 and unsupported coverage for `SELECT /*+ ORDERED */ 1;`.
- `tdd-lsp-baseline.log` records three unsupported diagnostics where the new contract expects a syntax diagnostic and one unsupported diagnostic.
- `tdd-first-green.log` records the first passing worker, corpus, and Validator/CLI checks after the predicate change.

The first complete v4 suite used manifest `d552f10f4b39f51ac4ac10704ba82497a42bf4368d51caada50e9e70be8de25b`.
After that suite passed, final source review added `scanner_support.c` to the explicit grammar input digest list.
That produced the final manifest above without changing admission or transport code.
The earlier artifact is retained as `pre-helper-binding-build`.
The final build repeated identity, rejected-library, corpus, native error/recovery, Validator/CLI, native LSP, and trace checks.

| Command or check | Actual result | Receipt |
| --- | --- | --- |
| `just test` | 124 tests passed | `core-tests.log` |
| `just test-lsp` | 34 tests passed | `lsp-tests.log` |
| `just test-native-parser` with pre-helper-binding manifest | 48 native tests and 20 adapter tests passed | `native-tests.log` |
| Six focused tests with final manifest | Identity, rejected library, error flags/recovery, 393 worker cases, 393 NativeWorker adapter cases, and Validator/CLI parity passed | `final-identity-native-tests.log` |
| `just test-lsp-native` with final manifest | 8 tests passed | `final-lsp-native-tests.log` |
| `python3 native/parser-worker/qualify.py --build native/parser-worker/build --output native/parser-worker/qualification` | 393 fixtures passed with final manifest | `final-qualification.log` and committed qualification results |
| `just build` after final helper binding | Wheel and sdist built | `final-package-build.log` |
| Copied-worker checks | valid, syntax-error, valid; old v3 pair rejected with U1001 | `copied-worker-check.json` |
| Preserved input checks | All original native inputs and primary build files retained their hashes | `preserved-inputs-check.json` |

The exact build command was:

```sh
python3 native/parser-worker/build.py \
	--source /home/vimkim/gh/cubrid-rust/reference-cubrid-cc947788 \
	--generated /home/vimkim/gh/cb/develop/build_preset_debug_gcc \
	--library /home/vimkim/gh/cb/develop/build_preset_debug_gcc/cs/libcubridcs.so.11.5 \
	--runtime-prefix /home/vimkim/.cub/install/develop/debug
```

The task checkout's default build directory is isolated from the primary checkout.
The final build log is `bound-source-build.log`.
The [machine-readable checks](../../../native/parser-worker/qualification/ordered-checks.json) bind the logs to each tested manifest.
The older `qualification/checks.json` remains historical v3 distribution evidence, not a claim about the new v4 artifacts.

## Corpus, ranges, and no-execution evidence

The retained corpus contains 393 cases, with 110 valid, 89 syntax-error, and 194 unsupported results.
The 68 new ORDERED cases contain 11 valid, 9 syntax-error, and 48 unsupported results.
Three new syntax cases are scanner lexical rejections and have no native observation.
The other admitted failures expose native parser errors with nativeErrorId zero and no internal error.
The native recovery test sends both hinted and unhinted valid requests after malformed hinted SELECTs in one process.
Every qualification response reports unchanged syntax settings.

For the mixed Unicode and CRLF fixture, Validator and CLI preserve S1001 at code-point span `[27, 53)` and U1002 at `[53, 82)`.
LSP converts these to UTF-16 ranges from line 0 character 28 to line 1 character 24, and from line 1 character 24 to line 2 character 27.
Changing the document to a valid hinted literal SELECT clears the diagnostics at the new document version.

The final trace observes one worker exec, no descendants, no network calls, and five writable opens, all inside its private worker directory.
It traces network, process, and openat calls for the exact 393-case corpus.
This is host-specific evidence and does not establish an operating-system sandbox or qualify arbitrary SQL.

The preservation check rehashed 16 runtime files, 4 generated headers, 8 original grammar inputs, 7 helper inputs, 618 source headers, and all 5 primary build files.
The source checkout remains clean at the pinned commit.
The final manifest additionally binds the unchanged `scanner_support.c` digest `b58ad8fe45c975e2282c3eb26ef7a1fe40fe2bd37416442a11e7488a4b03a5fb`.
An initial preservation script treated source-header keys as absolute paths and failed before completing. The corrected retained script resolves those keys against the pinned source root and passes.

## Remaining limits and handoff

No native safety blocker remains for the accepted literal ORDERED subset.
No claim is made for hints on table queries, hint arguments, other hints, generic SHOW, other CUBRID builds, other platforms, semantic validation, or SQL execution.
The full eight-environment release matrix and combined consumer acceptance belong to the root's follow-up verification and were not rerun by this ticket.
No editor installation, user settings, remote branch, or main commit was changed.

The checkout had no unrelated tracked changes at dispatch. Task files are committed.
The local build, Python environment, and package outputs are ignored disposable outputs. The valuable native artifact copy is retained outside the worktree.
No worktree removal, rebase, merge, push, deployment, or publication was performed.
