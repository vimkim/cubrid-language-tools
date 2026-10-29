# Bounded SELECT ORDERED qualification

Editor users need native checks for one audited optimizer hint without opening database-dependent parser paths.
This ticket starts at `49479b2d0a6cf39f71498834215346d8381b82c5` on `followup/native-ordered`.
The merge destination is `main`. Integration, push, installation, and publication require later approval.

## Accepted scope

Qualify one closed `/*+ ORDERED */` immediately after a top-level literal SELECT.
The hint name is ASCII case-insensitive. Space, tab, CR, and LF can surround the name.
Only those whitespace characters can separate SELECT from the hint. Ordinary comments can precede SELECT or follow the hint.
The body retains the existing literal SELECT alphabet of integers, strings, NULL, commas, and literal signs.
The native parser decides whether an admitted sequence is valid.

Closed malformed hints, arguments, duplicate hints, nested comments, other hints, line hints, and other placements remain unsupported.
An unterminated comment retains the existing scanner syntax error without a native call.
Queries with names, FROM, DISTINCT, arithmetic, CTEs, or subqueries do not gain hint support.
No public interface, mandatory dependency, SQL execution, connection, or editor installation changes are included.

## Acceptance

1. Audit the pinned lexer, grammar actions, hint helpers, recovery, and settings for source `cc947788d3b7dc402f46192d0f3299ddcc8563ba`.
2. Record failing tests through the real worker and public Validator before implementation.
3. Verify admitted, malformed, and unsupported forms with original Unicode and CRLF spans.
4. Verify unchanged settings, native error flags, and a valid follow-up request after rejection.
5. Bind the new coverage revision to the worker manifest and Python identity.
6. Run native tests, the retained corpus under strace, CLI and LSP parity, and proportionate core checks.
7. Preserve the primary worker and all pinned native inputs. Retain a copied qualified worker outside the task worktree.
8. Commit the source audit, corpus, bilingual coverage reference, and exact [ticket report](reports/native-ordered.md).

If the audited path or real worker evidence fails, retain unsupported coverage and record the reproducible blocker instead.
