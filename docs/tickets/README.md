# Central implementation tickets

This nine-ticket graph replaces the old eleven-ticket csql-future graph.
It delivers the independent engine and its standard adapters.
Separate editor, AI, and terminal work remains in the [long-term roadmap](../roadmap.md).

- [01: Independent completion library](01-completion-core.md) — dependencies: none.
- [02: Qualified native worker](02-native-worker.md) — dependencies: none.
- [03: Shared validation and lint CLI](03-lint-cli.md) — dependencies: 01, 02.
- [04: Offline schema snapshots](04-schema-snapshots.md) — dependencies: 01.
- [05: Shared LSP adapter](05-lsp.md) — dependencies: 03, 04.
- [06: Query and DML coverage](06-query-dml.md) — dependencies: 02.
- [07: Schema and engineer coverage](07-schema-engineer.md) — dependencies: 06.
- [08: CSQL script classification](08-script-boundaries.md) — dependencies: 03, 07.
- [09: Distribution and final qualification](09-delivery.md) — dependencies: 05, 08.

Initial frontier: 01 and 02.
Ticket 04 can proceed after 01. Ticket 06 can proceed after 02.
Exact dispatch commits and acceptance evidence live in [execution state](../orchestration/state.json).
