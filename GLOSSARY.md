# CUBRID language authoring

## Language

**Authoring part**:
A contiguous portion of SQL text eligible for conservative SHOW and optimizer-hint authoring checks.
It excludes CSQL commands and opaque procedural or trigger tails, and does not establish native parser coverage.
_Avoid_: qualified statement, complete statement

**Authoring finding**:
A conservative warning about a SHOW or optimizer-hint form in the selected language profile.
It does not establish native syntax validity or change native coverage.
_Avoid_: parser error, syntax verdict
