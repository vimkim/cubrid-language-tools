# Repair reviewed hint argument completion

Work item 606. Baseline is `38733ed3485b9065802bc768c19e3e03af60c88a`. The coordinator supplies this document's exact dispatch commit in the implementation prompt. Worktree is `/home/vimkim/gh/cubrid-language-tools-hint-repairs`, branch `fix/hint-identifier-edits`. The coordinator will fast-forward the feature branch after verification. Main integration retains its approval gate.

Read AGENTS.md, show-hint-authoring.md, show-hint-design.md and `/home/vimkim/temp/cubrid-show-hints-606-yszqo6t9/engine-review.txt`. That report contains three proven findings and exact API and framed-protocol reproductions. The disposable pinned-scanner probe proves the quoted-backslash counterexample at the scanner level only.

Commit failing public regressions before changing production code. Fix these bounded findings together:

1. Quoted and Unicode hint argument identifiers must use their full token replacement span and compatible quoting. Accepting `[order]` inside `[ord|er]` must not double brackets. Accepting `가나` inside `가|나` must not duplicate text. Preserve quote styles and Unicode code-point to UTF-16 conversion.
2. Hint argument suggestions must discover explicit aliases after owner-qualified relations such as `FROM dba.account a` without a schema snapshot. Reuse the existing relation parsing rules, consuming qualification before alias selection. Keep the data model local and avoid another partial parser with a separate rule list.
3. The malformed-argument checker must follow the pinned delimiter-specific backslash rule in `read_hint_args`. The valid two-backslash counterexample in the review must not receive A1002. Retain findings for genuinely unbalanced arguments and suppression for incomplete hint comments. Native coverage/status remain unchanged.

Add public `complete()` edit-application and pure-authoring counterexample tests plus real framed-LSP regressions for the replacement ranges and Unicode. Run focused tests and the existing core/protocol suites proportionate to these changes. Keep all earlier authoring, native coexistence and catalog checks green. Native CUBRID source/build/runtime and real editor settings stay read-only.

Accepted comment-review cleanup deletes only the narrating module docstrings at authoring.py line 1 and tools/check_show_hint_inventory.py line 2. Keep generated provenance, public function contracts, legal and source-derived fixture comments. Correct the stale broad provenance sentence that says profile never selects completion vocabulary; qualify it as the inherited non-hint vocabulary and retain the exact-profile hint section.

Update docs/tickets/reports/show-hint-authoring.md with exact red/green evidence, review corrections and remaining limits. Reread the diff, stage only task files, and commit the final repair. A task-owned environment and ignored qualified-native build link are ready. No subagents, integration into main, rebase, push or publication. Return the final SHA and concrete commands/evidence. Parent owns the independent final review and installed editor acceptance.
