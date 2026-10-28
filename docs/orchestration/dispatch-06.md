# Central ticket 06 dispatch

Baseline: `504541aaa08508f1fc096c2a44c661376e32136c`. Branch: `central/ticket-06`.
Checkout: `/home/vimkim/gh/cubrid-language-tools-06`.
Destination: `implement/central-engine` in the coordinator checkout.

Read root AGENTS.md, docs/spec.md, docs/contracts.md, docs/execution.md, docs/tickets/06-query-dml.md,
ticket02 report, native/parser-worker/AUDIT.md and README.md, personal CUBRID policy and TDD skill.
Use this one fresh context and isolated checkout for this bounded native qualification ticket.
The current nine-ticket graph is the Python stage of the accepted Python-PoC-then-Rust roadmap.

## Ownership

Own native/parser-worker coverage families, native worker/protocol adaptations, audits/notices/qualification fixtures and tests.
You may edit validation/profiles.py and validation/worker.py where required to validate expanded kind/coverage identities.
Preserve public WorkerConfig, NativeWorker and ValidationResult interfaces. Message coordinator before changing shared contracts.
Do not edit validation/__init__.py, validation/models.py, shared models, completion, schema, configuration, CLI, root packaging, recipes or uv.lock.
CLI03 owns its own shared service and configuration in parallel. It will consume NativeWorker unchanged.

## Qualification requirements

Qualify bounded forms covering SELECT, joins, expressions, CTEs/subqueries, INSERT, UPDATE, DELETE and MERGE as ticket06 requires.
Write and enforce conservative per-family feature predicates before native parsing. Native statement kinds alone cannot grant coverage.
Admit malformed sequences within audited token/features so native parsing still decides syntax; avoid replacing grammar with a second parser.
Reject unknown/unsafe features before native grammar calls. Handle comments, hints, strings and quoted names without broad accidental admission.
Audit every newly reachable reduction/helper, syntax parameter and error path against the exact source commit.
Never execute submitted text, open/connect a database, call compilation/session APIs, modify runtime/source, or launch daemons.
Catalog-dependent/internal failures remain unsupported/tool failures with accurate classifications; they cannot become ordinary syntax failures without evidence.
Keep original Unicode spans and explicit precision. Preserve the existing bounds, status/error/coverage invariants, cancellation and normal shutdown guarantees.
Update coverage revision, supported kinds, manifests/profile identities and corresponding tests consistently. Profile/build pin remains exact; no closest-version fallback.
Retain valid/malformed/incomplete/Unicode/mixed positive and negative fixtures for each admitted family and actual no-execution/network/descendant/external-write traces.
Keep old regression guarantees, adapting obsolete unsupported expectations where new audited coverage deliberately supersedes them.
If a family cannot be qualified, report the exact reachable-action/runtime evidence promptly and retain an honest incomplete checkpoint. Do not erase a criterion or claim broad support.

## Exact inputs

Source: /home/vimkim/gh/cubrid-rust/reference-cubrid-cc947788 at cc947788d3b7dc402f46192d0f3299ddcc8563ba (read-only).
Generated headers: /home/vimkim/gh/cb/develop/build_preset_debug_gcc.
Library: /home/vimkim/gh/cb/develop/build_preset_debug_gcc/cs/libcubridcs.so.11.5.
Library SHA256:56eb36e9a46e3b6f5258974b25085b81d1679430618041343e4d979704822b33.
Runtime prefix: /home/vimkim/.cub/install/develop/debug.
Follow native build/test recipes. Current develop source is newer; do not substitute its headers.

Run mandatory native/adapter corpus, full available suite and distribution checks. Preserve exact build/trace evidence and limits.
Write docs/tickets/reports/06.md with criterion evidence, commands/counts, baseline/commit and unrelated dirt.
Commit scoped result/report before review. No ticket integration, main merge, publication or deployment is authorized.
