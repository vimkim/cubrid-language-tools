# CUBRID language tools guidance

Read `/home/vimkim/my-cubrid/CUBRID.md` before CUBRID-specific work.
The user's instructions and personal CUBRID policies take precedence.

## Product ownership

This is an independent central language project.
The Python import package is `cubrid_language`.
The core owns completion, syntax checking, lint diagnostics, and shared values.
LSP and CLI adapters belong to this repository.
Editor products and csql-future remain separate consumers.
Preserve csql-future and the original checkpoint worktrees.

The core and CLI retain zero mandatory Python runtime dependencies.
The LSP adapter can use optional pygls dependencies.
Keep native parser details behind the qualified process interface.
Never execute submitted SQL for linting.
Treat unsupported coverage and native failures as explicit unsuccessful results.

## Execution

Use one fresh-context agent and isolated worktree per bounded ticket.
Read the ticket, specification, contracts, and exact dispatch baseline first.
Use TDD at public interfaces for new behavior.
Serialize shared recipe and packaging edits.
Record acceptance evidence and remaining limitations in the ticket report.
Use work-tracker item 572 for durable build state.

## Git and authorization

Inspect the branch, worktrees, status, and unrelated changes first.
From main, develop, or feature branches, use a sibling task worktree and topic branch.
Local task commits are authorized. Stage only task files.
Request approval before rebasing and integrating concrete ticket results into their destination.
After approval, inspect a clean expected destination, rebase, check, and merge with --ff-only.
The approved squash fallback applies when rebase and fast-forward are impractical.
Main integration approval includes a main push through its configured remote.
Other pushes, remote repository creation, publication, and deployment need separate authorization.
No remote exists at bootstrap. Report that fact rather than inventing a remote.
Preserve valuable artifacts before removing only merged task worktrees and branches without force.

This is a remote Linux host. Use headless automation and disable browser auto-opening.
For ordinary next-step requests, review the current session objective first.
After completion, report remaining work with `work-tracker list --here`.
Use an unscoped list only when the user asks what to do next today.
