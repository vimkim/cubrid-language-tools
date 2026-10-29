# CUBRID language tools

[한국어](README.md) | **English**

**One engine for CUBRID SQL completion and syntax checks across tools.**

`cubrid-language-tools` is an independent engine for CUBRID syntax, command, and
schema knowledge. It provides a completion library, an offline lint CLI, and
an LSP adapter for separate csql-future, VS Code, Neovim, and AI products.

**Validate a Python PoC first, then migrate gradually to Rust.**
The development release provides completion, CLI, optional LSP, and bounded V3 offline syntax checks.
The [VS Code extension](https://github.com/vimkim/cubrid-vscode) and [Neovim plugin](https://github.com/vimkim/cubrid.nvim) are public alphas.
See their repositories for editor installation and configuration. Install the shared Python server separately.

[Install and qualify](docs/install.en.md) · [Coverage](docs/coverage.en.md) · [Architecture](docs/architecture.en.md) · [Development and product roadmap](docs/product-roadmap.en.md) ·
[CLI and validation API](docs/lint-cli.en.md) · [Stdio LSP](docs/lsp.en.md) · [Documentation](docs/README.en.md)

## One engine, three interfaces

![Target architecture: csql-future calls the library, VS Code and Neovim use LSP, and AI and CI use the CLI. A Python PoC precedes gradual Rust migration. Strict checks use a native CUBRID worker.](assets/readme/architecture.en.svg)

| Interface | Purpose |
| --- | --- |
| **Library** | Direct requests for completion candidates and replacement spans in unfinished SQL |
| **Lint CLI** | Files/stdin, human/JSON diagnostics, and exit status |
| **LSP** | Shared completion and syntax diagnostics across editors |

The core owns context, identifiers, aliases, schema values, source positions,
and diagnostic contracts. Adapters own transport and lifecycle. Consumers own
their interfaces and metadata acquisition. Editors do not reimplement language knowledge.

## Local execution

Python consumers import the library. Editors spawn an LSP child process and use
stdio. The validator talks to an owned native CUBRID worker using JSON lines over
pipes. No shared daemon, TCP listener, or hosted service is required.

Strict checks use a qualified native parser instead of SQL execution or database
connections. Completion remains independent of parse success, including at an
unfinished `SELECT e.`. Missing parsers, unsupported forms, and syntax errors remain distinct results.

## Python PoC → validation → gradual Rust migration

1. **Python PoC:** prove completion, diagnostics, schema contracts, and CLI/LSP flows in `cubrid_language`.
2. **Shared corpus:** record valid, invalid, and incomplete SQL, Korean/emoji locations, and schema candidates as comparison evidence.
3. **Module-by-module Rust replacement:** compare candidate order, spans, diagnostics, and protocol results before replacement.

Consumers can use qualified Python interfaces while Rust migration continues.
Bindings or compatibility layers for direct Python imports will be selected at
the relevant stage. This plan does not replace the native CUBRID parser with a new Rust SQL grammar.

## Engine and consumer boundaries

- **This repository:** shared completion, syntax diagnostics, profiles, schema/source-range contracts, native worker, CLI, and LSP.
- **csql-future:** history, Ctrl+R, keys, completion menus, connections, and catalog acquisition.
- **VS Code / Neovim:** file associations, highlighting, indentation, and extension packaging.
- **AI / CI:** workflows and shared diagnostic result policies.

Current csql-future uses its own completion implementation. Migration requires
separate parity checks. Terminal usage and internal adoption material belong in
the [csql-future repository](https://github.com/vimkim/csql-future). Engine architecture and migration direction belong here.

## Support targets and roadmap

The Python PoC core and CLI run on Python 3.10+ with zero mandatory Python runtime
dependencies. LSP uses optional dependencies. Strict checks require a separately
qualified native runtime. The first parser target is Linux x86-64 and
**CUBRID 11.5.0.2704-cc94778**. Other builds and versions require separate qualification.

**Stdio LSP and offline syntax linting** are implemented. SHOW COLUMNS, DESCRIBE, DESC, and class-description EXPLAIN remain unsupported.
Completion retains 11.4 vocabulary provenance, distinct from strict 11.5 parser qualification.
Separate **VS Code and Neovim alphas** have locally verified completion, syntax diagnostics, highlighting, and indentation.
csql-future and AI consumer integration remain follow-up work. Later goals include **formatting with editor
integration**, semantic/style lint, and broader language coverage. Initial linting
means syntax diagnostics. See the [roadmap](docs/product-roadmap.en.md) for details.

## Contribute

Include your CUBRID version, shareable minimal SQL, expected candidates or
diagnostics, and actual results in an [issue](https://github.com/vimkim/cubrid-language-tools/issues).
Concrete examples guide the corpus and supported coverage.

## License

[Apache License 2.0](LICENSE). Preserve the [native notices](native/parser-worker/notices/README.md) and separately supplied runtime terms.
