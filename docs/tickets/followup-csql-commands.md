# CSQL session command text checks

Baseline: `49479b2d0a6cf39f71498834215346d8381b82c5`.

Admit complete column-one `;commit` and `;rollback` lines without arguments, and `;time on/off` and `;line-output on/off` lines. Preserve `;help`, `;exit`, and `;autocommit on/off`. Match ASCII case without Unicode normalization. Permit ASCII spaces or tabs between a command and its required argument and after a complete form. Preserve LF, CRLF, EOF and all original code-point spans.

The no-argument query forms of `;time` and `;line-output` are outside this ticket. Invalid or extra arguments, abbreviations, indentation, and other commands remain `CUBRID-U1002`, not syntax errors. Pending SQL, lexical blocks, and procedural regions retain their existing recovery behavior. Check all text after `;exit`. Require a qualified profile and worker even for command-only documents. This checks text shape only and never executes commands or simulates transaction or session state.

Pinned CUBRID source `cc947788d3b7dc402f46192d0f3299ddcc8563ba` lists the names in `src/executables/csql_session.c:92-94,112-113`. The handlers at `src/executables/csql.c:1219-1243,1426-1459` establish their semantics, including status output for non-on/off arguments. The English manual at `en/csql.rst:411-413,434-436,590-601,1462-1470,1508-1512` and Korean manual at `ko/csql.rst:409-410,432-434,588-599,1460-1468,1509-1513` document the commands. Manual checkout `3b6ae97bfbdc664b010ffa933ded5a05b291ae03` is documentation evidence and does not broaden the contract.
