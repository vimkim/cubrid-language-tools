# Editor onboarding and CI delivery

The core README now links the public Neovim and VS Code repositories. Both editor repositories have public installation guides and reproducible build, test and package workflows. The user approved integration and main pushes, including the eight existing local Neovim commits. csql-future migration was excluded.

## Published changes

| Repository | Integrated source | Result |
| --- | --- | --- |
| [cubrid-language-tools](https://github.com/vimkim/cubrid-language-tools) | Documentation `3780dbf147fad956147df29700ac718159147f68` | Both root READMEs link the editor repositories near the top. Bilingual installation and current publication status are corrected. The newer `just sync` and PATH guidance is preserved. |
| [cubrid.nvim](https://github.com/vimkim/cubrid.nvim) | `8e9f200e881f82241ced6dd01735b104ede0d203` | LazyVim startup spec, explicit extension selection, discovery/doctor guidance, extracted-package CI and bounded test deadlines. |
| [cubrid-vscode](https://github.com/vimkim/cubrid-vscode) | `afd459b7eb9a9a42164f0aa9ed191967c56a6e95` | Download-first VSIX guide, one package with required provenance, minimum/stable installed-desktop tests and accurate qualification status. |

The separately approved personal Neovim configuration commit `b51be9a` was already integrated and pushed. Its original unrelated dirt was restored exactly. Later configuration work belongs to another session and was not changed by this delivery.

## Neovim verification

[Hosted run 40834798245](https://github.com/vimkim/cubrid.nvim/actions/runs/40834798245) passed at `8e9f200`. The official Neovim 0.12.5 binary ran 17 portable invocations from the extracted plugin. All 34 archive files match the exact pushed source byte-for-byte. The hosted plugin archive SHA-256 is `dc52cfa76376d3a5c039f0d51888737b33fd6949f72ab7c0197bc30cee2683f2`.

Local qualification also passed the 17 portable invocations and all four native cases with the existing qualified worker/runtime. The later discovery cases were classified explicitly. `discovery-cases.lua` is portable; `discovery-doctor.lua` and `doctor-display.lua` remain in the mandatory native-inclusive full runner alongside integration and startup. Hosted CI does not claim native parser success.

Independent review found that TERM-only deadlines could wait indefinitely. A separate correction reproduced the problem before adding a five-second KILL grace period. The same control passed afterward, and the coordinator repeated it. The original four negative boundary checks ran after implementation and do not establish TDD.

## Microsoft desktop verification

[Run 40836324028](https://github.com/vimkim/cubrid-vscode/actions/runs/40836324028) qualified source `eb4cc32` on Microsoft Visual Studio Code 1.109.0 and freshly resolved stable 1.144.0. The package job and both desktop jobs passed. The coordinator and integration owner inspected all eight probe/controller receipts and the actual saved completion bytes.

Each version passed these mandatory cases:

- `portable` checked language association, real native-unavailable diagnostics, public suggestion acceptance with Korean/emoji and CRLF bytes, schema A/B/stale/C/disabled/inherit replacement, and two public restarts.
- `hanging-replace` checked replacement of an unresponsive initializer and recovery.
- `hanging-term` checked retirement of a TERM-resistant initializer before the real successor.
- `hanging-timeout` checked startup timeout, no automatic retry and recovery after a setting change.

All receipts identify Microsoft desktop, the expected editor version and installed extension path. Every SDK exit was successful. PID plus Linux start time identifies owned server processes; all recorded direct servers exited after the editor, without cleanup intervention. The package sidecar binds the clean source/workflow SHA, VSIX hash and 323 extension files. The installed `.vsixmanifest` is checked against the authenticated archive-root manifest.

The first qualified CI VSIX SHA-256 is `4113089fce0aed92a9c77f3674bf81f597afbb35a0bd7531f97c5deccca992f4`. Both desktop jobs consumed that package. The shared core was pinned to `2a8842c45c4fb219e322afd731c27937a107324f`; hosted Python was 3.10.22.

The qualification-status documentation was then published as `afd459b`. [Final automatic run 40837432286](https://github.com/vimkim/cubrid-vscode/actions/runs/40837432286) passed for that exact documentation tip. The coordinator replayed all eight final probe/controller receipts, package provenance and saved completion bytes. The final VSIX SHA-256 is `a3d29145bfda1979b14a91aa4b275d7b2c03104d90b42e62e6223bedca076c3e`. The changes are limited to both READMEs and the acceptance record. Runtime, workflow, settings examples and alpha download URL are unchanged.

Coverage is Linux x64, trusted workspaces and native inputs absent. Each case observes the real server's `CUBRID-T1001`. This does not qualify native syntax success on Microsoft desktop, untrusted workspaces, other platforms or arbitrary descendant cleanup.

## Repairs grounded in hosted evidence

The first hosted run failed before any desktop probe. The actual stable response contained historical suffixed release names, and the installer copied the VSIX root manifest to `.vsixmanifest`. The repair validates the selected current version and authenticates the copied file while retaining strict missing-file, extra-file, symlink, manifest and runtime tampering checks.

A further review caught inherited CI flags in the new regression test. The test now isolates and restores its environment. An ordinary-process preload tripwire demonstrated RED before the fix and GREEN afterward without any SDK download or local desktop launch. All 12 local tests passed with the fake hosted environment and tripwire.

Production extension code, lifecycle behavior, languageclient 9.0.1 and all eight production dependency resolutions were preserved. The original [v0.1.0-alpha.1 release](https://github.com/vimkim/cubrid-vscode/releases/tag/v0.1.0-alpha.1) and asset remain unchanged, with SHA-256 `621a757ddce1c33b7e9c624d312e66e4faddf21cbca11969720154f358b5f39b`. The guides distinguish that alpha's OpenVSCode evidence from qualified CI source builds.

## Preservation and cleanup

The approved rebase preserved Neovim's independently added SQL defaults, `file_extensions`, runtime discovery, doctor commands, new tests, acceptance records and generated-help-index ignore. The old documentation commit `72379ba` remains an ancestor. Core PATH installation recipes and guidance were preserved. Native inputs, original checkpoints, unrelated feature worktrees and the real user configuration were not changed by this integration.

Core documentation and all three merged Neovim task worktrees/branches were removed without force after checking preservation. VS Code and coordinator cleanup are being completed after the final run and record publication. No remote branch deletion, Marketplace publication, new alpha release or csql-future migration is included.

Prove It Works required inspecting real archives, installed artifacts, saved bytes and hosted receipts. Separate Before Serializing Shared State kept each writer and repository integration isolated.

## Evidence and audit

The evidence directory is `/home/vimkim/temp/cubrid-editor-hardening-c57_w98j`.

- `integration-core/docs-check.txt` records the rebased README links and retained PATH instructions.
- `integration-neovim/root-verified.json` records the exact source/archive comparison, hosted 17-case receipts and local four-case native results.
- `integration-vscode/run-40836324028/root-verified.json` and `inspection.json` record the first successful desktop qualification. The same files under `run-40837432286` record the exact final documentation tip. `integration-vscode/verify-hosted.cjs` repeats the coordinator check.
- `integration-vscode/run-40834804424` preserves the failed first run and actual boundary inputs.
- `vscode-hosted-boundary-fix/report.md` and `vscode-ci-test-env-fix/report.md` record RED/GREEN repairs.
- `vscode-qualification-docs/report.md` records the narrowly scoped status refresh.
- `docs/orchestration/editor-hardening-decisions.tsv` is the canonical append-only decision trail. `trail-audit.md` covers the earlier preparation handoff; a final available-model audit checks the approved integration and hosted evidence.

Review uses available GPT models. It does not claim cross-provider or different-model-family independence.
