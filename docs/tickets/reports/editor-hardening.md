# Editor onboarding and CI review

The user approved onboarding and editor CI, excluded csql-future migration, and requested prominent links to both vimkim editor repositories in the core README. The separately approved Neovim configuration integration is complete. New documentation and CI source integration is awaiting concrete approval under AGENTS.md line 35.

## Committed candidates

| Repository | Checkout and branch | Candidate | Result |
| --- | --- | --- | --- |
| Core | `/home/vimkim/gh/cubrid-language-tools-editor-docs`, `docs/editor-installation` | `7c2e723856320f2d57d6b95f2445178c90dd2115` | Both READMEs prominently link the public editor repositories; bilingual install/status guides corrected. |
| Core coordination | `/home/vimkim/gh/cubrid-language-tools-editor-delivery`, `delivery/editor-hardening` | Current report commit | Contract, state, plan and append-only decision trail. |
| VS Code docs | `/home/vimkim/gh/cubrid-vscode-editor-docs`, `docs/public-installation` | `5f905c7876fc5fb1736e94c32f57e2254dccd9fb` | Public alpha VSIX download/install first; shared server/native prerequisites. |
| VS Code CI | `/home/vimkim/gh/cubrid-vscode-ci`, `ci/desktop-qualification` | `620f0696ebbf4425a7b41c704222ab859323a392` | One VSIX/provenance build; hosted minimum 1.109.0 and freshly resolved stable consumers. |
| Neovim docs | `/home/vimkim/gh/cubrid.nvim-current-docs`, `docs/current-installation` | `64e911595fa6484242fd0b7c57ef1635909c4acf` | LazyVim startup spec and current extension-selection settings. Prior docs 72379ba is an ancestor. |
| Neovim CI | `/home/vimkim/gh/cubrid.nvim-ci`, `ci/portable-editor-checks` | `a94ea148ec3cec38ad1d3398e7381cbf61e75a1e` | Extracted-package portable CI; mandatory full native tests retained; bounded termination fixed. |

The public repositories are [cubrid.nvim](https://github.com/vimkim/cubrid.nvim) and [cubrid-vscode](https://github.com/vimkim/cubrid-vscode). The existing [VS Code alpha release](https://github.com/vimkim/cubrid-vscode/releases/tag/v0.1.0-alpha.1) remains unchanged.

## Verification

Core documentation passed link checks and independent status review. A disposable public clone installed the shared LSP extra. The refreshed LazyVim spec passed an isolated headless startup and extension-selection check, independently repeated by the coordinator.

The Neovim archive passed 16 portable invocations with the official 0.12.5 binary and exact core 2a8842c under Python 3.10.6. Both existing native cases passed on the qualified local host. Independent review verified archive/source correspondence, receipts, failure propagation and public settings. It found a TERM-only deadline defect. A separate fix reproduced RED first, added kill-after 5s, then passed GREEN. The coordinator repeated the control and rebuilt 28-file archive comparison. Full suites were not repeated for the final flag-only fix. The original four negative boundaries were checked after implementation, so they do not establish TDD.

VS Code passed 11 local tests, a production audit reporting 0 vulnerabilities, syntax checks, actionlint with shellcheck, and clean-commit package correspondence. The VSIX SHA-256 is `61ccd189dda7020d580807de6f6da85c07e9531451edbe446d7f8d42f6f2a62d`, with 323 extension files and a mandatory sidecar naming 620f0696. Independent review reran seven focused controller/package checks and checked the actual pinned core fixtures. The coordinator verified provenance, local desktop rejection, unchanged production code and all eight production dependency resolutions. No source comment findings remain; five redundant Neovim annotations were removed.

Prove It Works required checking extracted/packaged artifacts and actual process liveness. Separate Before Serializing Shared State kept documentation, packaging and orchestration writers in separate worktrees.

## Current destinations and preservation

A remote inspection at 06:55 UTC on 2026-10-29 found clean core main 1829fb6 equal to origin/main, clean VS Code main c6b2aea equal to origin/main, and clean Neovim main 90bd899 ahead of remote 4b4c4d9 by six commits. All origins point to the corresponding vimkim GitHub repositories. A later 07:03 UTC snapshot found clean Neovim main `6714657` ahead by eight commits. The two additions after `90bd899` are a live verification record and a generated help-index ignore. Detailed snapshots are in the evidence directory.

The Neovim CI/docs candidates were dispatched from b5c0c64. Main subsequently added native installation discovery, CubridDoctor/checkhealth, three discovery/doctor tests and a missing-runtime test adjustment in 90bd899. These later changes have not been verified by this ticket's pre-rebase suite. The approved rebase must preserve their implementation, new guide text and every test, classify native prerequisites, then run proportionate portable/full qualification before merging. The core's independently added just sync/uv-tool PATH recipes and guide section must also survive integration. This is the normal post-approval rebase and check gate, not permission to overwrite concurrent work.

The approved configuration commit b51be9a was merged and pushed, with the original lazyvim.json dirt restored exactly. Another session has since advanced the user configuration to a872ae2; its remote at the 06:55 UTC inspection was `90957f7` and lazyvim.json remains modified. That later configuration work is outside this ticket. Do not change, integrate or push it again here.

## Remaining gate

Approval covers rebasing these concrete docs/CI topics onto their current local main destinations, preserving concurrent changes, resolving conflicts, checking, fast-forward integration with the agreed squash fallback, and pushing each main through its configured origin. The Neovim push also publishes its eight already integrated local commits through `6714657`, covering SQL defaults, extension selection, runtime discovery, verification records and a generated help-index ignore. After that, inspect the automatically triggered hosted workflow runs and artifacts, correcting understood failures within the same scope.

No Microsoft desktop or new hosted workflow has run yet. Actual desktop 1.109.0 and freshly resolved stable must pass the installed-artifact, public completion, metadata, lifecycle, process and receipt gates. Hosted scope is trusted desktop with native inputs absent and real CUBRID-T1001 diagnostics. Native success is qualified only locally. No Marketplace publication, new alpha release, release overwrite, csql-future migration or deployment into the user's editor profile is included.

## Evidence

The evidence root is `/home/vimkim/temp/cubrid-editor-hardening-c57_w98j`.

- `nvim-integration/result.json` and `root-check.json` record the approved config integration.
- `core-docs/report.md`, `core-docs/correction/report.md`, and `docs-independent-review.md` record documentation checks.
- `neovim-docs-refresh/report.md` and `root-check-oww8k9gq` record LazyVim startup.
- `evidence/neovim-ci/report.md`, `neovim-independent-verification.md`, and `neovim-deadline-fix/report.md` record the artifact, review and correction.
- `evidence/vscode-ci/REPORT.md`, `evidence/vscode-independent-verification.md`, and `evidence/vscode-ci/root-check-9aduj49h` record the clean VSIX and local verification.
- `ci-design-verdict.md` compares both complete sketches and records the selected design/corrections.
- `review-state-*.json` records current branch, status, live remote heads and worktrees.
- `docs/orchestration/editor-hardening-decisions.tsv` is the canonical append-only trail. A final available-model trail review will be recorded before handoff.
