# Central ticket 02 dispatch

Baseline: `f2fb5c72b687b133627dcccc7ced398d5a0dbbf6`. Branch: `central/ticket-02`.
Checkout: `/home/vimkim/gh/cubrid-language-tools-02`.
Destination: `implement/central-engine` in the coordinator checkout.

Read root AGENTS.md, docs/spec.md, docs/contracts.md, docs/execution.md, and docs/tickets/02-native-worker.md.
Read personal CUBRID policy and TDD skill at /home/vimkim/.agents/skills/tdd/SKILL.md.
Read docs/research/parser-research.md and feasibility.md as historical evidence only.
Use only this fresh context for this ticket.

Reuse checkpoint 4a7f996b1d1b9f9c57b438856135f45218e2c5ab in /home/vimkim/gh/csql-future-language-02 read-only.
The old report docs/language-tools/tickets/reports/02.md lists unfinished qualification. Finish every new criterion.
Import shared Span from cubrid_language.models. Do not edit that file or __init__.py, completion, packaging or justfile.
You own validation/, native/parser-worker/, tests/native_parser/ and test_validation_*.py.
Use root recipes; request coordinator changes if needed. Avoid uv.lock conflicts by leaving it to coordinator/core ticket.

Pinned source: /home/vimkim/gh/cubrid-rust/reference-cubrid-cc947788.
Generated headers: /home/vimkim/gh/cb/develop/build_preset_debug_gcc.
Library: /home/vimkim/gh/cb/develop/build_preset_debug_gcc/cs/libcubridcs.so.11.5.
Library SHA256: 56eb36e9a46e3b6f5258974b25085b81d1679430618041343e4d979704822b33.
Runtime prefix: /home/vimkim/.cub/install/develop/debug.
Source commit: cc947788d3b7dc402f46192d0f3299ddcc8563ba. Profile: cubrid-11.5.0.2704-cc94778.
Current develop source is newer. Do not use its headers or change it, initialize databases or launch daemons.

Complete written reachable-action/settings audit, notices, deterministic internal-error fault injection confined to a test build, response-invariant checks, isolated runtime evidence, full available checks and packaging build.
Keep evidence source-specific and distinguish traced fixtures from an OS sandbox claim.
Record each criterion in docs/tickets/reports/02.md and commit scoped result.
No integration or push is authorized. Notify the coordinator when committed review is ready.
