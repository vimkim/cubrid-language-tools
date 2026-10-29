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
