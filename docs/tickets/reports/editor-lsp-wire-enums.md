# LSP wire enum acceptance report

## Result

The converter accepts legal `str` and `int` enum values in editor initialize requests. It constructs the declared lsprotocol enum after checking the exact wire type. Unknown enum values and nonmatching types fail for enum fields. Ordinary `int` and `str` fields retain exact-type validation.

Product baseline: `3bb70e492efe7bcb7de58a801281f7a088a9c39e`.
Dispatch baseline: `7654d343394e2e8474f47811747ec96dba5b4e07`. The worktree was clean and the product baseline was its ancestor. Failing test commit: `1084caf`. Fix commit: `d5a571eb03d543af1438b85933fcad3aed60f9f0`.

## Cause and choice

`cattrs` first dispatches by registered class and includes subclasses. The strict `str` and `int` hooks therefore receive targets such as `TraceValue`, `ResourceOperationKind`, and `CompletionItemKind`. Their exact-type check compared a JSON string or integer to the enum class and rejected legal values before enum construction.

A runtime probe using the pinned dependencies showed `default_converter()` constructs known enum members and rejects unknown values. It also converts `True` and `1.0` to `CompletionItemKind.Text`, and coerces primitive fields. Removing strict hooks or relying on default enum dispatch would weaken validation. The revised hook checks the exact underlying wire type before calling the declared enum constructor. It does not maintain an enum registry or change the public interface.

The core package and CLI still have no mandatory Python runtime dependencies. The optional environment used `pygls==2.1.1`, `lsprotocol==2025.0.0`, `attrs==25.4.0`, `cattrs==25.3.0`, and `typing-extensions==4.15.0` from the existing extra. The editable server is `/home/vimkim/temp/cubrid-lsp-enums-venv/bin/cubrid-language-server` and reads this task worktree.

## Verification

The new tests send framed JSON-RPC requests to the server process. The acceptance inputs include the original minimal `trace: "off"` request and capability subsets from Neovim and VS Code. They exercise string enums, integer enums, unknown enum values, wrong enum types, malformed fields, and the UTF-16 and full-sync response. Existing tests cover boolean, string, and float positions, malformed notifications, and protocol-only stdout.

Before the fix, the focused command below failed all three legal initialization subcases. The minimal response was `{'error': {'code': -32602, 'message': 'Invalid parameters for initialize'}, 'jsonrpc': '2.0', 'id': 1}`.

```sh
/home/vimkim/temp/cubrid-lsp-enums-venv/bin/python -m unittest discover -s tests/lsp -p test_protocol.py -k initialize_accepts_editor_wire_enums -v
```

The same command passed after the fix. The broader command below passed all three initialization tests.

```text
/home/vimkim/temp/cubrid-lsp-enums-venv/bin/python -m unittest discover -s tests/lsp -p test_protocol.py -k initialize -v
Ran 3 tests in 12.492s
OK
```

The full captured requests were replayed through framed stdio with `/home/vimkim/temp/cubrid-lsp-enums-replay.py`. Each response advertised UTF-16 and full synchronization.

```text
minimal initialize OK; utf-16; full sync
neovim initialize OK; utf-16; full sync
vscode initialize OK; utf-16; full sync
```

A live Neovim 0.12.5 headless session loaded the unchanged plugin at `/home/vimkim/gh/cubrid.nvim-alpha`, initialized the task server, attached a CUBRID buffer, and received `SELECT` completion. The probe is `/home/vimkim/temp/cubrid-lsp-enums-nvim.lua`.

```text
nvim --headless -u NONE -i NONE -l /home/vimkim/temp/cubrid-lsp-enums-nvim.lua
Neovim 0.12.5 initialized, attached, and received SELECT completion
```

Neovim also printed a plugin deprecation notice and a shutdown notification. Neither prevented the assertions from passing. Full consumer acceptance remains with the coordinator.

```text
/home/vimkim/temp/cubrid-lsp-enums-venv/bin/python -m unittest discover -s tests -v
Ran 109 tests in 6.061s
OK

/home/vimkim/temp/cubrid-lsp-enums-venv/bin/python -m unittest discover -s tests/lsp -v
Ran 30 tests in 40.168s
OK
```

## Existing validation limits

The dispatch baseline already accepted `capabilities: []` and `completionItemKind.valueSet: [true, 1.0, "1", 99]` through framed initialization. The latter uses the lsprotocol type `CompletionItemKind | int`, and cattrs leaves those union values unchanged. The former structures an empty list as an empty capabilities object. The primitive hook does not govern these cases. They remain unresolved and require a separate boundary validation change if the contract requires rejecting them. The regression instead checks invalid values in `insertTextMode`, an integer enum field without that union, and checks a scalar malformed capabilities value. No validation regression was observed in the existing strict position and notification tests.

No native parser, packaging, recipe, formal model, or consumer files were changed. The two captured editor payloads and live Neovim probe are local evidence, not committed fixtures. The server was installed editable for task acceptance and is not a release artifact. No rebase, integration, push, or deployment was performed.
