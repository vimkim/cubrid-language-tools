# Development and product roadmap

[한국어](product-roadmap.md) | **English** · [Documentation](README.en.md)

The development sequence is **Python PoC → verified behavior and stable contracts
→ gradual Rust migration**. The engine and its consumers release independently.
This document records goals, not release dates or implementation completion.

## 1. Prove workflows in Python

Use `cubrid_language` to prove completion, source ranges, schema values, and
diagnostics. Keep unfinished SQL eligible for completion. Use a separate native
CUBRID worker for strict parsing. Expose the same results through a file/stdin CLI and a stdio LSP adapter.

The first parser profile is `cubrid-11.5.0.2704-cc94778` on Linux x86-64.
Start with literal SELECT and CREATE SERIAL. Expand audited coverage for queries,
DML, schema, engineer statements, and mixed CSQL scripts. Missing parsers and unsupported forms cannot become syntax passes.

Core and CLI target Python 3.10+ with zero mandatory Python runtime dependencies.
LSP dependencies are optional. Native runtimes require separate qualification.
PoC completion and production release qualification are distinct milestones.

## 2. Establish shared evidence

Record these outcomes in a common corpus for Rust replacements and consumer integration:

- Ordered completion candidates for valid, invalid, and incomplete SQL/CSQL.
- Replacement spans for quoted identifiers, owners, aliases, tables, and columns.
- Code-point/UTF-16 conversion around Korean text, emoji, and CRLF.
- Diagnostic codes and statuses for syntax errors, unsupported coverage, and tool failures.
- CLI JSON/exits and LSP changes, cancellation, and removal of stale diagnostics.
- Exact parser identities, qualified coverage, and observations of no SQL execution or database connection.

Inherited terminal vocabulary includes 11.4 manual provenance. Keep that identity
distinct from strict 11.5 parser qualification. Record version-specific sources and coverage.

## 3. Replace verified modules with Rust

Choose bounded modules and migrate them individually. Compare identical inputs
against Python and replace a module after it meets its contracts.
Python and Rust implementations may coexist during the transition.

Select migration order from PoC evidence and dependencies. Verify shared values,
completion, validation adapters, CLI, and LSP at their respective boundaries.
Direct Python consumers also need a binding or compatibility layer before replacement.
No specific FFI technology or new Rust SQL grammar is selected in advance.

Preserve CLI/LSP protocols and observable results through the migration.
Record actual compatibility and performance evidence instead of attributing improvements to language choice alone.

## 4. Extend into separate consumer products

Consumers can use qualified Python interfaces before the entire Rust migration finishes.

| Product | Planned integration/features |
| --- | --- |
| csql-future | Use the shared completion library. Keep history, menus, connections, and catalogs in the terminal |
| VS Code extension | Dedicated `cubrid` identity, LSP completion/diagnostics, highlighting, indentation, opt-in `.sql` association |
| Neovim plugin | Filetype, built-in LSP, completion/diagnostics, highlighting, indentation, snapshot reload |
| AI / CI tools | Integrate structured lint results and failure states into workflows |

Terminal migration requires candidate, Unicode edit, and metadata parity plus
the existing PTY checks. Initial editor schema completion uses offline snapshots.
Automatic live editor connections are later work.

## 5. Broaden language support

- **Formatting:** develop a CUBRID SQL formatter and connect it to VS Code/Neovim formatting actions.
- **Highlighting:** evaluate Tree-sitter after initial editor lexical rules.
- **Semantic/style lint:** define separate rules, codes, and fix contracts after initial syntax diagnostics.
- **Completion:** extend result inference for CTEs, derived tables, correlated queries, and synonyms.
- **Syntax/platforms:** qualify PL/CSQL, other 11.5 builds, 11.4, and additional operating systems separately.

Formatting, semantic/style lint, and editor packages are not current delivered
features. See the [csql-future repository](https://github.com/vimkim/csql-future) for terminal features available today.
