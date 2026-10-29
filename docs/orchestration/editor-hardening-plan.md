# Editor onboarding and CI qualification

The user approved jobs 1 through 3 and excluded csql-future migration. The core README must visibly link both vimkim editor repositories. Work item 595 tracks this run.

## Done predicates

- Neovim config commit b51be9a is integrated into its current main and pushed under the explicit approval. Original lazyvim.json bytes and non-target plugin pins remain unchanged. Only its merged task worktree is removed without force.
- Core Korean and English READMEs link https://github.com/vimkim/cubrid.nvim and https://github.com/vimkim/cubrid-vscode. Public install documents describe the published alphas accurately and show reproducible setup without private host paths.
- Both editor repositories have reproducible build, portable test and package checks. Microsoft VS Code desktop runs the actual packaged integration on a suitable hosted runner at the declared minimum and stable version. A missing native runtime remains an explicit unsuccessful diagnostic, not native qualification.
- Actual hosted run results and package receipts support every compatibility claim. Local syntax/build checks do not substitute for desktop execution.
- Focused checks and independent review pass; task changes are committed. New docs and CI integration occurs only after concrete approval. Main push and merged-worktree cleanup follow that approval. No Marketplace publishing or replacement of the existing alpha release occurs.

## Workflow

- [x] Read the Principles section of poteto-mode.
- [x] Phase A: Frame. Inspect four repository states, the live Neovim deployment, published artifacts and official desktop testing guidance.
- [x] Phase B: Design the workflow. Ground the existing host harness, compare two desktop CI shapes and select a small artifact-based runner before implementation.
- [x] Phase C: Run the loop. Finish each bounded unit against its acceptance predicate.
- [x] Phase D: Keep the audit trail. Append decisions and evidence as each checkpoint completes.
- [ ] Phase E: Verify and hand back. Review real artifacts and hosted outcomes, with unresolved coverage kept explicit.

## Throughput checkpoint

The expected work is four repositories, three documentation surfaces, two editor CI adapters and one approved configuration integration. CI queue and desktop download time can extend the run. Rigor is high at Git integration and the desktop/package boundary; text-only changes use link and factual checks.

The root alone owns orchestration state, tickets, the tracker and the canonical decision trail. Core docs, editor docs, Neovim config integration and read-only CI design outputs have separate writers and worktrees. The CI implementer alone owns package.json, lockfile, workflows and test harness files. Documentation owners never edit those files. Native inputs and csql-future remain read-only and out of scope.

Swarm phases are Frame, Fan out, Aggregate and Report. Work is partitioned by ownership, not raced except for two read-only architecture sketches. Both sketches are judged before one CI implementation owner starts. Only actual runs can mark behavior VERIFIED.

## Architecture gates

Ground, Sketch, Agree, Implement and Scrap are the architecture phases. Agree has no extra user checkpoint. The desktop harness compares an installed packaged VSIX plus separate test probe with an extracted-package development host. Source-code-only or OpenVSCode-only results do not qualify Microsoft desktop. Hosted workflow publication/execution must respect the concrete Git integration gate. The current host never launches Electron, a GUI or forwarded X11.

## Authorization

The first explicit reply approved the reviewed Neovim configuration commit. The later yes at the active transcript line 4485 approved the concrete docs/CI packet, rebases, main merges and pushes, including eight existing local Neovim commits, and hosted execution. Those approved source integrations and hosted checks are complete. Final coordination-record publication uses the same approval.

The user did not request csql-future migration, Marketplace publisher registration, Marketplace publication, deployment of new editor builds into the real user profile, or a new GitHub alpha release.

## Local review checkpoint

Core documentation is published. The Neovim rebase preserved later runtime discovery, doctor tests, acceptance notes and the help-index ignore. Its hosted 17 portable and local four native cases passed. Microsoft desktop 1.109.0 and freshly resolved stable 1.144.0 passed all four mandatory cases each at the final published VSCode documentation tip. Actual archives and receipts were inspected. Final audit and coordination-record publication close work item 595.
