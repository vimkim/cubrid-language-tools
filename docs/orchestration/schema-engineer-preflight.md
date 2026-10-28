# DDL and engineer-statement preflight

These are source pointers for ticket07, not qualification evidence.
Every upstream pointer uses pinned source cc947788d3b7dc402f46192d0f3299ddcc8563ba.
Ticket07 must still audit complete reachable paths and test its admitted forms.

## SHOW cannot use one blanket predicate

[SHOW TABLES construction](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/parser_support.c#L6451-L6508) reads db_get_database_name and returns no node when it is absent.
[SHOW CREATE TABLE construction](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/parser_support.c#L7225-L7265) calls pt_help_show_create_table while building the query.
[Current-user SHOW GRANTS](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/parser_support.c#L7647-L7665) reads current authorization identity.
[Generic SHOW construction](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/parser_support.c#L6831-L6910) can perform a DBA check and resolve form-specific arguments.
Audit each exact form and its metadata callbacks before native admission.
A catalog-dependent parse failure cannot become a syntax rejection or pass.

## EXPLAIN spelling is release-specific

The [DESCRIBE/DESC/EXPLAIN alternatives](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L7796-L7802) share one production.
Its [statement actions](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L7213-L7255) describe a class through query-construction helpers.
Do not assume a generic EXPLAIN SELECT query-plan statement.
Audit the actual helper path and record the supported spelling/limits.

The [EVALUATE reduction](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/csql_grammar.y#L11055-L11069) allocates a PT_EVALUATE and attaches expression/target nodes.
That reduction alone does not evaluate the expression.
Qualification still needs its admitted expression paths, shared helper audit, fixtures and trace.

## Measured connection-guard barrier

Ticket07's transitive review found that class-description helpers call
[pt_dbval_to_value](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/parser/parse_dbi.c#L583-L598).
It ignores the return of db_value_clone.
That [clone wrapper](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/compat/db_macro.c#L1460-L1471) applies
[CHECK_CONNECT_ERROR](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/compat/db.h#L79-L90) before local cloning.

Probes of SHOW COLUMNS, DESCRIBE, DESC and EXPLAIN returned a tree with no ordinary/internal parser-list errors,
but er_errid reported ER_OBJ_NO_CONNECT (-224). These are rejected candidates, not qualified coverage.
The production extension clears error state before parsing and observes the native error manager afterward.
Unreported native failures cannot become passes. The four known forms are denied before native parsing.
The prior query/DML corpus and other admitted new forms report zero native error id under this guard.

The user was asked whether to defer these forms or expand to a separately qualified parser-only backend.
Until that decision, the original describe-family acceptance criterion remains incomplete.
Do not set connection/user state or ignore the error to force success.
