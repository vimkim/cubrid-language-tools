# Shared source interpretation acceptance

Completion and authoring now share one owner for tolerant tokens and eligible authoring parts.
The existing public interfaces and observed results remain unchanged.
The [ticket](../shared-source-interpretation.md) records the user-approved narrow design and preservation requirements.

## Checkout and commits

The product baseline is `3b9d5af67e530423aa6a9e435b06cb8d629c9e5b`.
The exact implementer dispatch was `3b45d480e8871233322697d825a5e5083e11cf99`, which changed only the ticket and glossary.
Work item 649 tracks this refactor; work item 572 retains the central build context.

The checkout is `/home/vimkim/gh/cubrid-language-tools-source-interpretation`, branch `refactor/shared-source-interpretation`, with `main` as the integration destination.

| Commit | Result |
| --- | --- |
| `3b45d480e8871233322697d825a5e5083e11cf99` | Record the bounded ticket and authoring vocabulary. |
| `b3b008ddadbcdd40d654387582c907e6b74ddbbf` | Pin three public characterization tests before production changes. |
| `f6ce81d5791b2fe7cf2be8e5ac2ed9eaf50fb015` | Move source ownership and migrate both callers. |
| `7a05b12ca5ccafde545c1c1fea03ccab11d8c30b` | Remove three redundant private docstrings. |

Production and artifact acceptance below refer to `7a05b12`.
The acceptance-report commit changes documentation only.
No rebase, main integration, push, publication, or global installation has occurred.

## Structure and preserved behavior

`cubrid_language._source` owns the existing `Token`, `unquote`, and `tokenize` implementations.
It also owns immutable `AuthoringPart` values and `authoring_parts`.
Each part pairs an original-document span with tokens relative to the part's start.
The existing classifier and conservative trigger cutoff determine eligibility.
Authoring consumes the retained tokens instead of scanning the eligible slice again.

Completion retains its whole-document, session-argument, and hint-argument lexical origins.
It reads hint eligibility from the shared parts.
The old definitions, `sql_parts`, and deferred imports are removed; no forwarding functions were added.
The existing one-way hint-inventory import remains.

This removes the completion-to-authoring-to-completion call path.
The classifier, native checks, validation aggregation, LSP lifecycle, configuration, acquisition, package exports, dependencies, and recipes are unchanged.
No cache, generic adapter, new public interface, or SQL execution path was added.
Future maintenance benefits are a design expectation, not a measured result.

## Behavior pin and differential evidence

The three characterization tests passed against unchanged production before the move and against the implementation afterward.
They cover malformed command-line quoting, trigger cutoff and command-separated recovery, and validation before unknown-profile return.
Existing tests retain identifier quoting, Korean, emoji, CRLF, incomplete hints, and token-left-edge replacement coverage.

The frozen corpus contains 163 inputs with 1,341 completion and 326 authoring observations.
Its SHA-256 is `2226eed01ef1b821e3150bd8865d1510a5b0f3a080b267a6082a5a7470e1c716`.
The coordinator captured 15 additional public input and profile observations from the unchanged baseline.
All 1,682 observations matched both final task source on Python 3.14.0 and the independently installed core wheel on Python 3.10.6.
Checks include ordered result values, spans, allowed state, diagnostic order, and exception types and messages.
The verifier records exact import paths and source hashes and rejects a different frozen corpus.

Independent Spec review also compared the moved tokenizer definitions by AST, excluding docstrings.
They matched the baseline.
A deterministic 504-input check compared all 469 returned authoring parts with a fresh scan of each exact slice; all token tuples matched.
These are finite checks, not a proof for every possible input.

## Executed checks

Evidence is retained under:

`/mnt/nvme/data-5/tmp/architecture-review-20261031T060336Z/candidate-01-design/`

| Check | Observed result and receipt |
| --- | --- |
| Repository `just test`, using a task-owned Python 3.14.0 environment | 159 passed. `project-core.log`. |
| Installed core wheel, Python 3.10.6, isolated imports | 159 passed. `installed-core.log`. |
| Installed LSP wheel with optional dependencies, Python 3.14.0 | 35 passed over real Content-Length stdio frames. `installed-lsp.log`. |
| Frozen public replay against final source | All 1,682 observations matched. `final-source-public-check.json`. |
| Frozen public replay against installed wheel | All 1,682 observations matched. `installed-public-check.json`. |
| Installed CLI and dependency checks | Lint retained missing-worker failure and the exact authoring warning span. Version and absent-optional-server behavior passed. No pygls in the core-only environment. `installed-cli-check.json`. |
| Wheel and source archive checks | 22 package modules, 19 license files, 207 source files, three commands, and six optional-only requirements passed. `final-artifacts.log`. |
| Installed source identity | All 22 installed Python modules matched the wheel byte for byte. `installed-cli-check.json`. |
| Standards review | No documented breach or actionable heuristic finding. `standards-review.md`. |
| Spec review | No missing requirement, scope creep, or demonstrated implementation defect. `spec-review.md`. |
| Comment review | Three private docstrings removed. No MUST KILL findings, external-rule uncertainties, restored comments, or reruns. `comment-review.md`. |
| Diff and scope checks | `git diff --check` passed. Protected production paths and public exports are unchanged. |

The two review axes remain separate.
Standards had zero findings; Spec had zero findings.
Reviews used independent GPT agents; no cross-family review is claimed.

The built artifacts are in `final-dist` under the evidence directory.

| Artifact | SHA-256 |
| --- | --- |
| `cubrid_language_tools-0.1.0.dev0-py3-none-any.whl` | `041b1048fd2d9dd6d49607dc3c61ac0bd74adec37e3564df183ddf0ba95c3566` |
| `cubrid_language_tools-0.1.0.dev0.tar.gz` | `34968090835a30adb6627381b85e1b7e33ad854336d5f84ff934a2f4a4b6e813` |

## Initial environment failures

The implementer's shared-environment core run had two failures.
Its installed metadata lacked the schema entry point when task source was selected without task packaging metadata.
The normal project environment and independently installed wheel have the correct entry point and pass the complete suite.

The held-open-stdin cancellation test sends SIGTERM after a fixed 0.1-second delay.
It returned `-15` on both unchanged main and the candidate in the bytecode-disabled shared-environment run.
The coordinator inspected Linux `SigCgt` before sending the signal: neither process had registered its SIGTERM handler in those fixed-delay observations.
Waiting for handler registration before sending the same signal produced exit 130 on both versions, with empty stdout and the existing redacted cancellation message.
`stdin-cancellation-probe.json` records all four observations.
No acquisition or cancellation code was changed.
The fixed startup delay remains timing-sensitive; the normal project and installed-wheel core runs passed.

## Reproduction and limits

Run the repository core suite with `just test`.
The acceptance run used `UV_PROJECT_ENVIRONMENT` outside the checkout and `UV_PYTHON` pointing to the existing Python 3.14.0 interpreter.
Run framed tests in an installed optional-LSP environment with:

```sh
python -I -m unittest discover -s /home/vimkim/gh/cubrid-language-tools-source-interpretation/tests/lsp -v
```

`verify_public_parity.py` in the evidence directory replays the frozen corpus and public boundaries.
Supply the candidate's `--source-root` and `--package-root`, the frozen `--reference` and `--boundaries` paths, and a new `--output` receipt.
Omit `--source-root` for an installed package and use its site-packages directory as `--package-root`.
The baseline-capture script refuses a changed baseline or replacement of different saved observations; do not use capture as candidate verification.

No new native-parser qualification, live database run, real editor acceptance, performance measurement, or global installation was performed.
The core and LSP transport evidence does not claim broader native grammar coverage.
The root glossary remains repository documentation; the unchanged source-archive manifest does not include it.
No unrelated tracked or untracked changes were present in either checkout at acceptance.
Main integration and its configured push remain the user's next approval decision.
