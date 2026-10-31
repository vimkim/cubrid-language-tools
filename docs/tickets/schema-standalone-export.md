# S645. Standalone CSQL schema export

The user reported that Neovim schema acquisition rejected `csql -udba demodb -S`.
The same request succeeded after changing only `-S` to `-C`.
Add standalone mode to the shared exporter so the existing editor transport can use it unchanged.

The exact dispatch is `/home/vimkim/temp/cubrid-schema-standalone-645/dispatch.md`.
The baseline is `8f6dbcc5b791c0ca87268315e75ce281f6953639`.
Work in `/home/vimkim/gh/cubrid-language-tools-standalone-export` on `schema/standalone-export`, with `main` as the integration destination.
Read `AGENTS.md`, `/home/vimkim/my-cubrid/CUBRID.md`, `docs/spec.md`, `docs/contracts.md`, and the [schema export contract](../schema-export.en.md).
The [S636 report](reports/schema-export.md) records the original delivery.

Accept `-S` and `--SA-mode` for standalone mode. Preserve omitted mode and `-C` or `--CS-mode` as client/server mode.
Store one validated mode in immutable `Connection` and launch CSQL with exactly that mode.
Accept repeated aliases for one mode. Reject mixed modes and standalone endpoints with a host suffix before child launch.
Keep credentials, fixed catalog SQL, request and snapshot versions, deadlines, bounds, cancellation, and cleanup behavior.
Acquisition failures remain unsuccessful, redacted, and empty on stdout. Do not retry in another mode or change database services.

Use public-interface TDD for stdin requests, direct argv, and the importable API.
Prove that exported metadata loads for completion, client/server defaults remain compatible, and standalone failures and timeout cleanup stay bounded.
Update the bilingual reference and replace any release guard that requires standalone rejection.
Record failing-before evidence, passing checks, and limitations in the [S645 report](reports/schema-standalone-export.md).

One implementer owns repository edits and commits. Root owns work-tracker item 645, central context item 572, and isolated native/editor checks.
The Neovim repository and user configuration remain read-only dependencies.
Rebase, main integration, pushes, publication, and global installation require separate authorization under `AGENTS.md`.
