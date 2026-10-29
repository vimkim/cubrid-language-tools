# Editor hardening dispatch contract

Read AGENTS.md, the personal CUBRID policy, this contract and the exact baseline in editor-hardening-state.json before editing. Preserve unrelated user files, zero mandatory core dependencies and native inputs. Never execute SQL for verification. Never launch a desktop GUI on this host.

## Core documentation ticket

Owner scope is core README.md, README.en.md and user-facing Markdown below docs, excluding orchestration, tickets/reports and historical specifications. Add prominent direct vimkim Neovim and VS Code repository links in both root READMEs. Correct obsolete publication status. Describe shared server installation separately from native syntax runtime requirements. Verify any new installation command using a disposable environment; do not change user tool installation or native runtime. Use technical-writing and unslop. Commit on docs/editor-installation, baseline2a8842c. No push, rebase or integration.

## Editor documentation ticket

Owner scope is README.md and README.en.md in the two editor documentation worktrees, plus the Neovim help installation section if needed. Add a verified LazyVim spec that registers .csql during startup, public repo and alpha VSIX links, shared-server prerequisites, native parser/runtime pairing and explicit alpha limits. Preserve opt-in .sql and trust boundaries. Do not edit package.json, lockfiles, workflows, application source or acceptance history. Commit each repo separately from baseline c6b2aea and4b4c4d9. No push, rebase or integration.

## Approved Neovim config integration

Use the existing clean install-cubrid-nvim topic worktree. The user explicitly approved commit b51be9a. Back up and preserve the actual main's unrelated lazyvim.json modification and ignored lock pins. Clean the destination reversibly, rebase onto current local main, run a focused real-profile check, fast-forward, push its configured main remote and verify inclusion. Restore unrelated dirt byte-for-byte. Remove only the merged task worktree/branch without force. No other profile edits or upgrades. Report any understood remaining original dirt.

## CI grounding and design

Read current VS Code test/host scripts and Neovim tests/run.sh and identify portable versus qualified-native checks. Design real Microsoft desktop verification on GitHub-hosted Linux, including minimum1.109.0 and stable with observed version receipts. Do not run Electron locally. Prefer an actual installed VSIX and public editor commands with a separate test probe; compare a concrete alternative and explain the tradeoff. Preserve original alpha artifacts. Full native syntax qualification is not available on hosted runners; explicitly test missing-runtime diagnostic behavior and label scope. Only the future CI owner edits package/recipe/harness files.

## Core documentation review correction

The independent documentation review identified current publication-status contradictions in docs/roadmap.md and three prose locations in docs/architecture.html. A fresh correction owner may edit only those two files on the existing clean core documentation topic. The HTML scope is text-only status/link correction; CSS, scripts, diagrams and the dated architecture decision stay unchanged. Preserve AI and csql-future migration as future work. This is a current-status correction within the public documentation job, not an architecture redesign.

## Concurrent Neovim baseline refresh

After initial dispatch, another session integrated Neovim SQL-default behavior and related tests. Current main at inspection is 9a8b068, including ac9cf68 and 0f60ec9. Preserve that work and its missing-default.lua/sql-defaults.lua tests. Neovim now defaults both SQL and CSQL to cubrid; sql=false opts out. VS Code remains .sql opt-in. New Neovim documentation and CI are prepared from a fresh current-main worktree, without reverting the newer product behavior. Original 72379ba remains historical evidence, not the final merge candidate. The real Neovim config's independent 3071756 update is out of scope and must not be altered.

## Selected CI implementation

Use design-astra/design.md and shape.md as the base, with every correction in ci-design-verdict.md under the evidence directory. Two independent complete sketches and the judge agree on an installed VSIX plus a separate rejecting official test probe. No framework or production lifecycle copy is needed. Required provenance is a sidecar uploaded with the package and consumed by both desktop jobs. Official SDK calls run in supervised owned subprocesses, not promise-only timeouts. Server configuration is executable-only, so fixture arguments use inherited case environment or generated executable files. PID/start-time identities separate observed product exit from test cleanup. Native absence and trusted-workspace scope remain explicit.

VS Code CI owner alone owns package.json/package-lock.json, .vscodeignore, test/desktop, necessary test fixtures and .github workflows in its isolated CI worktree. Neovim CI owner alone owns tests/run-portable.sh, necessary composition of tests/run.sh, package verification scripts and .github workflows in its isolated current-main CI worktree. The full native suite remains mandatory and is rerun on the qualified local host if composition changes. Docs owners never edit these packaging or harness files. No application behavior change, source rebase, main integration, push, Marketplace publication or alpha asset replacement is authorized at this preparation stage.

Actual Microsoft desktop execution is only on hosted CI after concrete workflow integration approval. Local syntax/build/control-fixture/headless-Neovim checks prepare review; none counts as desktop proof.

## Latest concurrent extension-selection amendment

Before implementation dispatch, Neovim main advanced again to b5c0c6483583ca5d609169cd1b52336040e1292f. Both new Neovim worktrees now start there. The file_extensions replacement list selects .sql and .csql independently; the old sql option is rejected with migration guidance. Preserve tests/file-extensions.lua and updated SQL tests. This amendment supersedes the older sql=false instructions above. Core main separately added uv tool PATH installation recipes and docs; preserve those additions during eventual approved integration. No real user configuration changes are in scope.
