# SHOW and optimizer-hint authoring design

## Goal

Provide CUBRID SHOW and optimizer-hint completion and precise authoring warnings through the existing shared API, CLI, and LSP. Neovim uses the standard LSP connection. VS Code consumer changes, CSQL session enhancements, formatting, and broader native qualification are deferred.

## Shape

Keep `complete(text, cursor, profile, schema=None)` and `Validator.validate(text, profile, script_mode)` as the primary interfaces. Add a pure public authoring-diagnostic function for callers without a native runtime. Put the versioned language inventory, tolerant hint contexts, and targeted checks behind a small domain interface. Split packaged data from behavior if its size warrants it. Completion and lint read one authoritative inventory.

Authoring findings have category `authoring`, warning severity, exact original code-point spans, and stable `CUBRID-A` codes. Preserve the existing native status, coverage, statement kinds, failure diagnostics, and CLI exits. Clean authoring checks do not establish native validity. Missing native configuration still produces its tool error alongside safely computed authoring warnings. Unknown profiles receive no guessed closed-world findings.

Run input validation before scanning. Combine diagnostics once, deduplicate exact values, sort deterministically, and apply the configured total limit. Overflow must produce a visible tool diagnostic and unsuccessful status. Prioritize native failures when retaining bounded output. The smallest supported limit must retain the failure context even when it cannot fit separate entries.

Package the qualified inventory with source commit and evidence. A development-only extraction/check tool compares all pinned hint spellings and aliases with the inventory. Runtime use needs no source checkout. Unknown SHOW names require an exhaustive pinned grammar head inventory. Completion patterns alone are not a strict validator. Audit argument and placement checks separately, with valid counterexamples.

Hint contexts recognize block and line hint forms. Ordinary comments, quoted values, uncertain incomplete constructs, CSQL commands, and opaque procedural regions suppress authoring findings. Tolerant completion may operate inside an unfinished hint. Preserve full-token suffix replacement and Unicode/CRLF positions. Native validation receives original text unchanged.

## Neovim configuration

Ship `lsp/cubrid.lua`. Neovim's native LSP manager is the sole lifecycle owner. Convenience setup registers detection and trusted options and enables that configuration by default. An explicit setup opt-out leaves activation to native user or LazyVim configuration. Standard cmd, capabilities, callbacks, and settings overrides follow documented native order.

Retain existing discovery, doctor, file-extension selection, restart, schema reload, complete effective settings replacement, and owned manual completion behavior. Default activation shares one stable-root client across buffers. Explicit user root overrides can change that behavior. Standard configuration must also work without setup when a buffer is marked `cubrid`.

## Synthesis decision

The base is the coordinator's unified sketch. An independent runner supplied the warning-only aggregation direction but no completed package before it was stopped. The coordinator completed that sketch. The separate composition candidate proposed a new combined result type and broadened `syntax-error` semantics. Those changes were rejected because warning composition can preserve existing public semantics.

An independent Terra judge selected the unified design, scoring it 17/20 against 15/20. Grafts from the separate candidate are reproducible inventory provenance and detailed real-editor lifecycle acceptance. This is independent design review, without a cross-provider claim.

## Verification

Capture public failing regressions before production edits. Keep existing completion parity and native coverage suites green. Exercise the pure API, CLI, real framed LSP, extracted Neovim artifact, and Blink's LSP-only automatic popup and acceptance. Verify warnings clear after correction and cannot arrive from superseded document versions. Verify process cleanup, startup settings races, user overrides, and one actual default client.

Each implementation ticket uses a fresh implementer and isolated worktree. Local commits are authorized. Integration and publication retain their approval gates.
