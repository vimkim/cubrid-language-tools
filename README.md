# CUBRID language tools

One maintained language engine for CUBRID completion, syntax checking, and lint diagnostics.
This independent project owns the Python library, native parser worker, lint CLI, and optional LSP adapter.
VS Code, Neovim, AI checkers, and csql-future are separate future consumers.

![A shared library serves the LSP adapter, CLI, and future Python TUI](docs/architecture-assets/library.svg)

Explore the [interactive architecture](docs/architecture.html), [specification](docs/spec.md),
[public contracts](docs/contracts.md), [implementation tickets](docs/tickets/README.md), and [long-term roadmap](docs/roadmap.md).

## Current state

Implementation is in progress. These commands and interfaces are delivery targets until their tickets pass.
The first parser target is the exact CUBRID 11.5 development build `11.5.0.2704-cc94778` on Linux x86-64.
Other builds and platforms require separate qualification.
Completion remains available for unfinished SQL and when strict parsing is unavailable.
The initial linter reports syntax, unsupported coverage, and tool failures.
Semantic and style rules are future work.

The Python import package is `cubrid_language`. Core and CLI require Python 3.10+ with no mandatory Python runtime dependencies.
Strict checking also requires a separately qualified native runtime.
The language server will use optional LSP dependencies.
This repository currently exists locally and has no configured remote.

## Local processes

The engine runs locally. Editors spawn the language server and exchange LSP messages through stdin/stdout.
The server or lint CLI spawns its native parser worker and exchanges JSON lines through pipes.
csql-future will import the completion library directly after migration.
No localhost socket, TCP listener, network access, or database connection is required for these language operations.
“Central” means one maintained codebase and release, not a shared running daemon.
Each consumer owns the processes it starts. The hosted design in the comparison page is an alternative, not the selected design.

## Ownership

The core accepts document text, a cursor, an explicit parser profile, and optional schema metadata.
It owns language decisions and canonical source ranges.
Adapters own transport, editor lifecycle, or output formatting.
Consumers own their user interfaces and catalog acquisition.
No consumer should implement another CUBRID completion or syntax engine.

The existing csql-future terminal engine remains in place until its separate migration passes parity checks.
