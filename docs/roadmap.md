# Long-term work

The current implementation goal is the Python central engine and its library, CLI, and LSP adapters.
The accepted [public product roadmap](product-roadmap.en.md) adds gradual Rust migration after Python behavior and contracts are verified.
The [ticket graph](tickets/README.md) tracks that work.
Consumer products stay separate and use the same maintained language implementation.

## Finish the central engine

- Completed foundation: pure completion, offline snapshots, and exact-profile literal SELECT/CREATE SERIAL qualification.
- Deliver shared configuration, lint CLI, and LSP.
- Expand audited query, DML, schema, and engineer-statement coverage.
- Handle CSQL script boundaries and qualify installation, notices, and release artifacts.

## Separate consumer projects

- VS Code extension: dedicated `cubrid` language identity, `.csql` association, opt-in `.sql` mapping, lexical highlighting, indentation, server configuration, and extension-host tests.
- Neovim plugin: file detection, highlighting, indentation, built-in LSP setup, snapshot reload, and headless editor tests.
- AI checker: structured `cubrid-lint` integration, stable failure handling, CI examples, and workflow-specific policy.
- csql-future migration: depend on the central library, convert existing catalog values, preserve terminal menus and metadata acquisition, and remove its duplicate completion implementation after parity checks.

Consumer work starts after the relevant central interfaces pass their delivery gates.
The terminal migration requires completion corpus parity, Unicode edit parity, metadata parity, and the existing terminal/PTY suite.
Each consumer owns packaging and releases independently.

## Rust migration and formatting

- Compare bounded Rust replacements against the shared Python corpus before replacing each module.
- Preserve CLI/LSP results and choose Python bindings or compatibility layers before changing direct library consumers.
- Keep the qualified native CUBRID parser; a new Rust SQL grammar is not selected.
- Develop SQL formatting and editor formatting actions as a separate later feature.

## Language depth

- Qualify a parser-only backend for SHOW COLUMNS, DESCRIBE, DESC, and class-description EXPLAIN without connection state.

- Add explicit semantic rules using optional metadata, with separate codes and clear limits.
- Add configurable style rules and deterministic fixes after rule contracts exist.
- Extend completion scope inference for CTEs, derived tables, correlated queries, and synonyms.
- Qualify PL/CSQL and additional SQL/CSQL constructs separately.
- Track completion vocabulary provenance against the selected 11.5 source/manual.

## Profiles and maintenance

- Qualify subsequent 11.5 builds and 11.4 as separate profiles.
- Add platform builds and test native runtime compatibility on each platform.
- Define release compatibility, deprecation policy, and downstream upgrade tests.
- Add performance budgets, fuzzing, and large-corpus regression checks as supported coverage grows.
- Consider an additional language-neutral local interface only when a real consumer needs more than LSP or CLI.
- Consider a hosted engine only if a concrete remote-use requirement justifies its operational cost.

No hosted engine, automatic runtime download, or consumer repository publication is included in the current local build.
