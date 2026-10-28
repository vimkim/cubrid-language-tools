# CUBRID language tools

A central CUBRID language engine with library, LSP, and CLI interfaces.

The project is under implementation. The first target is the pinned CUBRID
11.5 development build recorded in the implementation specification.

The central project owns completion, syntax checking, lint diagnostics, dialect
profiles, source ranges, and schema snapshot contracts. VS Code, Neovim, agent
workflows, and csql-future are independent consumer projects. Their migration
follows a verified central engine.

Implementation proceeds in isolated task worktrees with reviewed local commits.
No remote repository or package publication is configured by this bootstrap.
