# PATH installation evidence

Ticket: [Install the CLI and LSP on PATH](../uv-tool-install.md).
Dispatch baseline: `2a8842c45c4fb219e322afd731c27937a107324f`.
Worktree: `/home/vimkim/gh/cubrid-language-tools-uv-install`.
Branch: `chore/uv-tool-install`. Integration destination: `main`.

## Delivered behavior

`just sync` installs both `cubrid-lint` and `cubrid-language-server` through
`uv tool install --reinstall '.[lsp]'`. `just install` aliases that recipe.
Repeating either command reinstalls the local checkout with its pinned LSP extra.
Package metadata and core runtime requirements are unchanged.

Both installation guides now describe the PATH commands, reinstall behavior,
`uv tool update-shell`, the server's argument-free stdio transport, and the
separate native worker requirement.

## Failing checks before implementation

At the dispatch baseline, both commands exited 1:

```text
$ just --dry-run sync
error: justfile does not contain recipe `sync`
$ just --dry-run install
error: justfile does not contain recipe `install`
```

After implementation, both dry runs exited 0 and printed the same installation
command. Tool versions were uv 0.9.11 and just 1.58.0. Local
`uv tool install --help` confirms that extras belong in the package specification.
That command has no `--extra` option in this uv version.

## Installation and executable checks

Evidence is preserved outside the checkout at
`/home/vimkim/temp/cubrid-uv-install-597.1gIuLT`.
The following commands ran from the ticket worktree. Both installation commands
exited 0. The tool directories did not exist before the fresh install.

```sh
evidence=/home/vimkim/temp/cubrid-uv-install-597.1gIuLT
UV_TOOL_DIR="$evidence/tools" UV_TOOL_BIN_DIR="$evidence/bin" just sync
python3 "$evidence/smoke.py" --bin-dir "$evidence/bin" --output-dir "$evidence/fresh"
UV_TOOL_DIR="$evidence/tools" UV_TOOL_BIN_DIR="$evidence/bin" just install
python3 "$evidence/smoke.py" --bin-dir "$evidence/bin" --output-dir "$evidence/reinstall"
python3 -m unittest discover -s tests -p test_lsp_bootstrap.py -v
git diff --check
```

The fresh installation built the local package and installed six packages and
two executables. The repeated installation rebuilt the package, uninstalled six
packages, installed six packages, and restored both executables. Logs are
`sync.log` and `install.log`.

Both smoke runs passed on Python 3.14.0. Each run started the installed commands
from its own empty directory outside the checkout, removed `PYTHONPATH`,
`PYTHONHOME`, and `VIRTUAL_ENV`, and disabled user site packages. Inspection with
the installed interpreter's `-I` option confirmed imports from the uv tool's
`site-packages`. Installed metadata keeps all six requirements behind the `lsp`
extra. The five applicable optional dependencies match their pinned versions.

Each smoke run verified these public behaviors:

- `cubrid-lint --help` exited 0 and described `--parser-worker`.
- `cubrid-language-server` started with no arguments and returned framed stdio
  initialization with UTF-16 positions and full document synchronization.
- Completion for `-- 가😀\r\nSELtail` returned `SELECT`, replacing characters
  0 through 7 on line 1 when requested at character 3.
- Shutdown returned null, exit completed with code 0, and stderr had no traceback.
  Stdout contained protocol frames only.

Each smoke output directory preserves `result.json`, `installed.json`,
`protocol.json`, CLI help output, and LSP stderr. The existing bootstrap checks
passed both tests, including imports without optional packages and the missing
extra's stderr guidance with exit 3. Their output is in `bootstrap.log`.

The standalone smoke script accepts any installed bin directory. To check a later
user installation, choose a new output directory:

```sh
python3 /home/vimkim/temp/cubrid-uv-install-597.1gIuLT/smoke.py \
  --bin-dir /home/vimkim/.local/bin \
  --output-dir /home/vimkim/temp/cubrid-uv-install-597.1gIuLT/user-install
```

## Limits and handoff

This ticket verified isolated tool installation on Linux with Python 3.14.0.
It did not rerun the existing release qualification across Python versions or
build native parser artifacts. Strict diagnostics still require a separately
qualified native worker and runtime. This ticket did not install tools globally,
change shell configuration, rebase, merge, push, or alter other worktrees.

The initial checkout had only the parent-created ticket as an untracked file.
The committed scope consists of that ticket, this report, the justfile, and the
two installation guides. Preserve the external evidence directory for review
and the later user-install smoke check.
