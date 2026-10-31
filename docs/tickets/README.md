# Central implementation tickets

This index preserves the completed nine-ticket graph and later work.
The engine and its adapters are integrated into public main. The editor alphas are public.
AI and terminal migration remain in the [long-term roadmap](../roadmap.md).
For current behavior, use [coverage](../coverage.en.md) and [installation](../install.en.md).
Reports and dispatch records retain the commit, test scope, and pending review state from when each was written.

- [01: Independent completion library](01-completion-core.md) — dependencies: none.
- [02: Qualified native worker](02-native-worker.md) — dependencies: none.
- [03: Shared validation and lint CLI](03-lint-cli.md) — dependencies: 01, 02.
- [04: Offline schema snapshots](04-schema-snapshots.md) — dependencies: 01.
- [05: Shared LSP adapter](05-lsp.md) — dependencies: 03, 04.
- [06: Query and DML coverage](06-query-dml.md) — dependencies: 02.
- [07: Schema and engineer coverage](07-schema-engineer.md) — dependencies: 06.
- [08: CSQL script classification](08-script-boundaries.md) — dependencies: 03, 05.
- [09: Distribution and final qualification](09-delivery.md) — dependencies: 05, 07, 08.

All nine tickets were integrated through `implement/central-engine` and are now in main. Ticket 07 passed its revised bounded scope with four accepted description exclusions.
The original description-qualification criterion did not pass. Ticket 09 completed delivery qualification at `f66072d`.
Independent source review passed at `96d6fb5`, and all corrected installation checks passed at `4c756d6`.
The full eight-environment ticket 09 distribution matrix is historical v3 evidence. It has not been rerun for v4.
Original dispatch commits and acceptance evidence remain in [execution state](../orchestration/state.json).

Dependency refinement after ticket 05: script classification uses the stable Validator seam independently of ticket 07.
Ticket 09 retains its direct ticket 07 qualification gate, confirmed passed by the coordinator on 2026-10-29.

## Integrated follow-up work

- [SHOW and optimizer-hint authoring](show-hint-authoring.md) implements the [selected design](show-hint-design.md).
- [Native ORDERED](native-ordered.md) adds the bounded v4 literal SELECT hint. Its [report](reports/native-ordered.md) preserves qualification evidence.
- [CSQL command text checks](followup-csql-commands.md) expands command shapes without execution. See its [report](reports/followup-csql-commands.md).
- [PATH installation](uv-tool-install.md) and [server version options](server-version.md) provide the documented install and command interfaces.

These follow-ups are present at core commit `057e41b0c02d85d09905301f6bfccbb7ed0b8965` on public main.
Current source, native, LSP, installed-wheel, and OpenVSCode checks are summarized in [installation evidence](../install.en.md#qualification-evidence).

## Schema acquisition

- [S636 schema export](schema-export.md) added explicit shared CSQL acquisition and the additive `schemaConfigured` reload result. Its [report](reports/schema-export.md) records source, installed-package, and real CSQL evidence.
- [S645 standalone schema export](schema-standalone-export.md) adds explicit standalone mode. Its [report](reports/schema-standalone-export.md) records verification and remaining limits. Local integration requires approval.
