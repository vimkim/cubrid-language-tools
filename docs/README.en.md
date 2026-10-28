# Documentation

[한국어](README.md) | **English**

Korean is the default language for user documentation. Each document links to its English edition, named `*.en.md`.
Code, commands, and protocol identifiers remain consistent across languages.

| Document | Read it to |
| --- | --- |
| [Project README](../README.en.md) | Understand the engine and consumer boundaries |
| [Install and qualify](install.en.md) | Install local core or optional artifacts and run mandatory release checks |
| [Qualified coverage](coverage.en.md) | Check the exact V3 profile, examples, exclusions, and results |
| [CLI and validation API](lint-cli.en.md) | Install, lint files, configure metadata, and own a validator |
| [CSQL batch scripts](scripts.en.md) | Check command boundaries, original spans, and conservative recovery limits |
| [Stdio LSP](lsp.en.md) | Install the optional server, configure editors, and use snapshots, completion, and diagnostics |
| [Architecture](architecture.en.md) | Understand the library, CLI, LSP, native parser, and separate consumers |
| [Development and product roadmap](product-roadmap.en.md) | Follow Python PoC, gradual Rust migration, and editor plans |

The development release implements the library, CLI, optional LSP, and bounded V3 syntax checks. Final review and integration remain in progress. `csql-future` is a
separate project and has not migrated to this engine. These documents distinguish planned central/editor features from available terminal features.

Terminal usage and adoption material belong in the [csql-future repository](https://github.com/vimkim/csql-future).
