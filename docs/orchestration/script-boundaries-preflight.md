# CSQL script boundary preflight

This is preparation for ticket08, not implemented script coverage.
Manual snapshot: clean develop at3b6ae97bfbdc664b010ffa933ded5a05b291ae03.
Pinned executable source: cc947788d3b7dc402f46192d0f3299ddcc8563ba.
The manual documents intended behavior; the exact source identifies this profile's dispatch paths.

## Batch context and interactive exception

The [English manual](https://github.com/cubrid/cubrid-manual/blob/3b6ae97bfbdc664b010ffa933ded5a05b291ae03/en/csql.rst#L342-L380) documents semicolon-prefixed commands, unique abbreviations and case-insensitive names.
It also describes strings, comments and delimited identifiers as lexical blocks.
Its sentence beginning with “Except in interactive mode” is ambiguous.
The [Korean paragraph](https://github.com/cubrid/cubrid-manual/blob/3b6ae97bfbdc664b010ffa933ded5a05b291ae03/ko/csql.rst#L348-L379) explicitly places the block-override exception in interactive mode.

The pinned [dispatch condition](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/executables/csql.c#L947-L959) agrees with that Korean reading: an interactive session can dispatch a prefix while inside a block; batch dispatch requires no current block.
The [block-state function](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/executables/csql_support.c#L1520-L1536) lists C comments, string states and double/backtick/bracket identifiers.
The [line-state update](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/executables/csql.c#L975-L1008) preserves that context between batch lines.

The lint document models files/batch text, not interactive control actions.
A line containing ;exit inside an open string/comment/identifier must remain SQL content.
Test multiline lexical blocks, CRLF and escaped/doubled quotes before extracting commands.

## Leading whitespace needs a conservative policy

The manual's [help summary](https://github.com/cubrid/cubrid-manual/blob/3b6ae97bfbdc664b010ffa933ded5a05b291ae03/en/csql.rst#L389-L413) says blanks/tabs may precede a command prefix.
However, the pinned main dispatch checks line_read[0]; the batch path uses [raw fgets](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/executables/csql.c#L859-L864), and the preceding processing handles [line endings/BOM](https://github.com/CUBRID/cubrid/blob/cc947788d3b7dc402f46192d0f3299ddcc8563ba/src/executables/csql.c#L918-L947).
Do not silently certify indented commands from the manual summary alone.
Review the complete pinned path. Keep unproven spellings unsupported rather than inventing normalization.

## Deliberate initial subset

Only exact full ;help, ;exit and ;autocommit on/off forms are requested initially.
Case variants can follow documented case insensitivity. Abbreviations and extra arguments remain unsupported unless separately qualified.
The real interpreter also accepts ! as a dispatch prefix (csql.c:109); shell/include/buffer-control forms remain unsupported and are never executed.
The [autocommit section](https://github.com/cubrid/cubrid-manual/blob/3b6ae97bfbdc664b010ffa933ded5a05b291ae03/en/csql.rst#L604-L609) describes optional arguments, but the initial contract deliberately requires on/off.

Classify original spans without executing commands or following include paths.
Preserve original SQL chunks and translate local diagnostics back to document code-point offsets.
Unqualified procedural blocks must not turn their internal semicolons into independent successful SQL checks.
Keep uncertain opaque regions unsupported and document recovery limits.
A document containing only accepted commands still requires profile/worker availability checks before a complete pass.
The checker inspects document text; it does not simulate runtime effects such as exiting or changing autocommit.
EOF-without-semicolon, mixed syntax+unsupported diagnostics and priority must stay consistent across library, CLI and LSP.
