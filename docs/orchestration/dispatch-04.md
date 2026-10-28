# Central ticket 04 dispatch

Baseline: `8d61ec87cd3fe5d80427e36ccd241e550180649a`. Branch: `central/ticket-04`.
Checkout: `/home/vimkim/gh/cubrid-language-tools-04`.
Destination: `implement/central-engine` in the coordinator checkout.

Read root AGENTS.md, docs/spec.md, docs/contracts.md, docs/execution.md, docs/tickets/04-schema-snapshots.md, and the TDD skill.
Ticket01 is integrated and verified. Use one fresh context for this bounded ticket.

Own a small `cubrid_language.schema` module (or an equivalently clear module), snapshot tests, and docs/tickets/reports/04.md.
Use existing immutable Relation/Schema values and pure complete(...). Do not edit their models, completion, native files, packaging, recipes or uv.lock.
Expose explicit loading and refresh interfaces that CLI and LSP can share. Keep filesystem work out of complete(...).
The caller resolves configured relative paths against the configuration directory in ticket03.
Preserve required/optional schema fields and spelling. Unknown fields are ignored; invalid required fields/types reject the snapshot.
Schema version must be integer1, not bool. Optional system must be bool. Names/column/index/user lists retain spelling and become immutable tuples through models.
Use no network, database access, executable commands or credentials.

Initial failure returns no schema and an explicit availability message. Failed refresh retains last valid schema with an explicit stale message.
An explicit refresh/configuration event is enough; no watcher is required.
Test absent/valid/invalid/changed snapshots and public completion results from loaded metadata, including Unicode.
Run focused tests, full available suite and build. Request coordinator packaging changes if extra test fixtures need inclusion.
Record each criterion, commands/counts, baseline, commit, unrelated dirt and limitations in reports/04.md. Commit scoped work.
No ticket integration, main merge or publication is authorized. Notify coordinator when reviewable.
