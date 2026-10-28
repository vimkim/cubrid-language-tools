# Central ticket 03 dispatch

Baseline: `504541aaa08508f1fc096c2a44c661376e32136c`. Branch: `central/ticket-03`.
Checkout: `/home/vimkim/gh/cubrid-language-tools-03`.
Destination: `implement/central-engine` in the coordinator checkout.

Read root AGENTS.md, docs/spec.md, docs/contracts.md, docs/execution.md, docs/tickets/03-lint-cli.md,
the integrated reports 01/02/04, and the TDD skill.
The accepted public product roadmap describes Python PoC then gradual Rust migration. This ticket implements the Python stage only.
Use this one fresh context and isolated checkout for this bounded ticket.

## Ownership

Own shared configuration, a configured document Validator, CLI formatting/entry-point modules, and new focused tests.
Suggested locations: cubrid_language/config.py, validation/service.py, cli.py and tests/test_config.py/test_validator.py/test_lint_cli.py.
You may export Validator from validation/__init__.py. Keep root exports small.
The shared packaging edit slot is assigned only to you for the cubrid-lint console script in pyproject.toml and its uv.lock update.
Native06 will not edit packaging. Ask coordinator for any other shared recipe/build changes.
Preserve the accepted Korean-first README and English companion. Put technical API/CLI instructions in a scoped document and link consistently.
Do not edit native/, validation/worker.py, profiles.py, positions.py, validation/models.py, shared models, completion or schema.py.
Native06 owns grammar/coverage/worker changes in a separate branch. Use its interfaces without duplication.

## Behavior and tests

Implement explicit trusted WorkerConfig ownership through Validator.validate(text, profile, script_mode), close/context cleanup, stable result priority and no ambient executable/runtime discovery.
A missing configuration produces explicit tool availability failure, including empty documents. Invalid modes/input/config produce T1003. Unknown profiles are not silently substituted.
The library owns language decisions. CLI owns input acquisition, path identity, human/JSON formatting and exits.
Read source paths/stdin as bytes and decode strict UTF-8. Preserve CRLF and original code-point spans. Never run CSQL, SQL, a shell command, or connect to a database.
Implement the exact CLI/exit/JSON and per-file error requirements, including invalid flags exit3 and one stdin read.
.csql defaults to csql mode; others/stdin use sql unless overridden. Full mixed-script classification is ticket08, so current unsupported commands must stay explicit.
Define and document project keys profile, scriptMode, schemaSnapshot. Only metadata keys belong in project config; reject executable/runtime/command/credential settings.
Resolve snapshot paths against each config file directory. Follow field precedence explicit flags, explicit config, nearest ancestor config, defaults. Keep that reusable for LSP.
Trusted worker/runtime values come only from explicit flags/caller settings, never project metadata or PATH search. Do not download runtimes.
Use currently stable unsupported fixtures such as CREATE PROCEDURE or shell/include constructs rather than table SELECT, whose coverage06 will add.
Keep default just-test independent of ignored native artifacts. Put actual native CLI qualification tests under tests/native_parser/ and fail visibly when their prerequisites are absent.

## Native qualification inputs

Pinned source: /home/vimkim/gh/cubrid-rust/reference-cubrid-cc947788.
Generated: /home/vimkim/gh/cb/develop/build_preset_debug_gcc.
Library: /home/vimkim/gh/cb/develop/build_preset_debug_gcc/cs/libcubridcs.so.11.5.
Runtime prefix: /home/vimkim/.cub/install/develop/debug.
Use native/parser-worker/README.md/root recipes to build your own worker, or an explicit trusted existing build for tests.
Do not edit pinned sources/runtime or create databases/daemons.

Run public library/config/CLI tests, actual installed console-script/native checks, full available suite and build/distribution checks.
Record every criterion, exact commands/counts/baseline/commit, unrelated dirt and limitations in docs/tickets/reports/03.md.
Commit scoped work before reporting. No ticket integration, main merge, push or deployment is authorized.
