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
- [08: CSQL script classification](08-script-boundaries.md) — dependencies: 03, 05.
- [09: Distribution and final qualification](09-delivery.md) — dependencies: 05, 07, 08.

Tickets 01 through 08 are integrated. Ticket 07 passed its revised bounded scope with four accepted description exclusions.
The original description-qualification criterion did not pass. Ticket 09 owns delivery qualification and remains pending final review.
Exact dispatch commits and acceptance evidence live in [execution state](../orchestration/state.json).

Dependency refinement after ticket 05: script classification uses the stable Validator seam independently of ticket 07.
Ticket 09 retains its direct ticket 07 qualification gate, confirmed passed by the coordinator on 2026-10-29.
