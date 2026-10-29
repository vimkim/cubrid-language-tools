# Install the CLI and LSP on PATH

Dispatch baseline: `2a8842c45c4fb219e322afd731c27937a107324f` (`main`).
Destination: `main`. Worktree: `cubrid-language-tools-uv-install`.
Branch: `chore/uv-tool-install`.

Read [the specification](../spec.md), [contracts](../contracts.md), and
[delivery ticket](09-delivery.md) before implementation.

The package already defines `cubrid-lint` and `cubrid-language-server`.
The user requests equivalent `just install` and `just sync` commands that install
both executables on the user PATH through uv, with working optional LSP dependencies.

Use a single installation recipe with a just alias. Install the local package
with its `lsp` extra and refresh an existing installation on subsequent runs.
Keep core/CLI runtime dependencies optional and native workers separately supplied.
Update the Korean and English installation guides.

Demonstrate the missing public recipe before editing it. Verify fresh and repeated
installation in isolated uv tool directories, CLI help, and real stdio LSP
initialization/completion outside the checkout. Do not add tests that merely
compare recipe text or duplicate its implementation.

Record commands, outcomes, baseline, and remaining limitations in
`reports/uv-tool-install.md`. Commit only this ticket's files.
Do not rebase, merge, push, or modify other worktrees.
