# Central CUBRID language engine specification

Architecture A was accepted on 2026-10-28: one independent project contains the shared library, LSP adapter, and lint CLI.
This specification supersedes the earlier csql-future monorepo implementation plan.
The [contracts](contracts.md) define observable behavior. The [tickets](tickets/README.md) define delivery gates.

## Product and ownership

Maintain CUBRID language knowledge once in `cubrid_language`.
Provide tolerant completion and strict offline diagnostics through small interfaces.
Keep native parser types and process handling inside the validation implementation.
Keep language decisions out of LSP, CLI, and consumer code.

The central repository owns:

- Immutable text ranges, completion values, schema values, diagnostics, and profile identities.
- Pure completion for incomplete SQL and supported session commands.
- Qualified native syntax checking without database connections or submitted-text execution.
- JSON schema snapshots, shared project configuration, a batch CLI, and an optional stdio LSP adapter.
- Coverage manifests, fixtures, notices, and release qualification.

Separate future projects own VS Code and Neovim integration, AI workflows, and the csql-future terminal interface.
The central build does not modify these consumers.
The [roadmap](roadmap.md) retains their work and the later migration gate.

## First support target

The user selected CUBRID 11.5 first.
The initial strict parser profile is `cubrid-11.5.0.2704-cc94778`.
It binds source commit `cc947788d3b7dc402f46192d0f3299ddcc8563ba`, matching generated headers, native library, runtime assets, syntax settings, and Linux x86-64.
Qualification applies only to this exact profile.
There is no nearest-version fallback.
Completion vocabulary inherited from csql-future includes 11.4 manual provenance.
Retain that provenance and report the difference from strict 11.5 parser qualification.

Initial parser coverage is literal SELECT and CREATE SERIAL.
A conservative predicate must admit a form before native parsing.
Auditing one statement kind does not qualify every construct within that kind.
Native parsing, error collection, tree checks, and internal-error checks must all succeed before a form passes.
A missing runtime, unknown profile, or unqualified construct cannot become a syntax pass.
The research evidence establishes feasibility, not a release claim.

## Central delivery scope

1. Port pure completion into an installable independent package without a csql-future runtime dependency.
2. Complete native-worker qualification and process isolation for the first exact profile.
3. Deliver shared validation/configuration and the offline lint CLI.
4. Load and refresh offline schema snapshots for all adapters.
5. Deliver LSP completion and diagnostics with correct document versions, cancellation, and UTF-16 ranges.
6. Qualify queries and DML: SELECT, CTEs, subqueries, joins, expressions, INSERT, UPDATE, DELETE, and MERGE.
7. Qualify CREATE/ALTER/DROP TABLE, VIEW, INDEX, SERIAL, and release-valid engineer statements.
8. Classify mixed CSQL scripts without execution and preserve original source ranges.
9. Qualify packaging, installation, adapter parity, notices, and the final supported coverage matrix.

Each expanded grammar family requires a reachable-action audit, explicit settings, positive and negative fixtures, and observed no-execution behavior.
Unsupported PL/CSQL, includes, shell commands, and other unaudited forms remain explicit unsupported results.
Engineer statements include SHOW, DESCRIBE/DESC, release-valid EXPLAIN, EVALUATE, statistics, tracing, transactions, and settings.
The pinned source determines the valid spellings and safe parse paths.

## Interfaces and distribution

`complete(text, cursor, profile, schema=None)` is deterministic and performs no I/O.
Strict validation uses a configured owned worker process through a shared validation interface.
The CLI and LSP convert those same results into their own transport formats.
Schema acquisition stays with the caller. Editors use offline snapshots initially.
The terminal can supply its existing catalog values after migration.

Use Python 3.10+ and zero mandatory Python runtime dependencies for core and CLI.
Use optional pygls dependencies for LSP and pin the implementation's tested versions.
Keep native artifacts separately built and bound to qualification manifests.
Do not vendor the full CUBRID source tree.
Cross-platform artifacts, automatic downloads, semantic lint, and style lint require later work.
