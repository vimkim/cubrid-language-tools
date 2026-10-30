# S636. Shared CSQL schema export

The user wants Neovim schema completion from a selected CSQL connection. This ticket delivers the reusable acquisition adapter and one-shot CLI. The Neovim consumer is a separate ticket.

The exact dispatch is `/tmp/cubrid-schema-implementation-EMmkLi/contract.md`, synthesized from two design candidates. Read it with `docs/spec.md`, `docs/contracts.md`, and `AGENTS.md` before implementation. The starting central baseline is `ad9d9434f6f8d74b8c44d9cadba0faf2362e6606`. Work in `/home/vimkim/gh/cubrid-language-tools-schema-export` on `schema/csql-export`; main is the integration destination.

Deliver `cubrid-schema export`, a standard-library-only acquisition module, strict connection and catalog boundaries, bounded owned POSIX subprocesses, version 1 metadata snapshots, and packaging registration. The editor request uses versioned JSON on stdin. Preserve pure completion and offline validation. Do not change LSP/config/completion/validation/native implementation or csql-future.

Use public-interface TDD. Record initial failing evidence, final test commands and results, exact source/fixture identities, redaction and process cleanup checks, and remaining limitations in `docs/tickets/reports/schema-export.md`. Update product contracts and current bilingual usage documentation to describe explicit acquisition. Keep historical acceptance evidence scoped to its original commits.

Local task commits are authorized. Commit meaningful changes before review. Main integration, push, global installation, publication, and deployment require the authorization described in AGENTS.md. Root owns the isolated native CSQL environment and cross-repository acceptance. Work item 636 tracks this delivery; item 572 retains the central build history.
