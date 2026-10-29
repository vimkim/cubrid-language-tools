# Query the installed language server version

Dispatch baseline: `f8b98c79682197b9b5d3587adc9e4897131e08ed` (`main`).
Destination: `main`. Worktree: `cubrid-language-tools-server-version`.
Branch: `feat/server-version`. Work-tracker follow-up: 614. Engine record: 572.

Read [the specification](../spec.md), [contracts](../contracts.md), and the
exact dispatch baseline before implementation.

Users need to identify the installed `cubrid-language-server` version without
starting an editor or an LSP session. The installed baseline rejects `--version`
with exit status 3 and says that the server accepts no arguments.

Add a standalone `--version` query to the existing dependency-free bootstrap.
Print `cubrid-language-server <installed version>` on stdout and exit 0.
Read the version from installed `cubrid-language-tools` distribution metadata.
Do not copy a version constant, read checkout files, or invent a source-only version.
Missing metadata must produce a clear stderr error and exit 3, without a traceback.
Provide `--help` and `-h` so users can discover the query.

Keep version and help independent of optional LSP packages and native runtimes.
With no arguments, retain stdio startup and its existing missing-extra guidance.
Reject unknown options and mixed or extra arguments with exit 3 and empty stdout.
Keep normal protocol stdout free of CLI text.

Use TDD at the public launcher interface. Prove metadata lookup with a version
that differs from the current development version. Check missing metadata,
help, malformed arguments, and the existing no-argument behavior.
Verify built console scripts outside the checkout in isolated core-only and
LSP-enabled installations, including a framed initialize/completion/shutdown.

Update the paired installation and LSP guides. Record the chosen design,
commands, outcomes, throughput checkpoint, baseline, and remaining limitations in
`reports/server-version.md`.

Do not change the package version, lint CLI, server lifecycle, LSP serverInfo,
native parser, editor consumers, installation recipes, or packaging configuration.
Only this ticket's owner edits implementation files. Commit task files locally.
Do not rebase, merge, push, install globally, or modify other worktrees.
