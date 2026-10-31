# Native worker identity diagnostics

Work 656, 2026-10-31. Engine baseline `bd7cd64291e240d2a4d0b36840b63be51e437fef`.
Task branch `fix/native-identity-details`. Local `main` integration requires approval.

The previous warning said only `worker identity differs from qualified profile`.
A configured v3 worker therefore failed against the current v4 core without identifying the stale coverage revision.
The CUBRID profile and Python package version still matched.

The shared adapter now reports sorted differing fields, expected and actual JSON values, trusted worker and manifest paths, and recovery instructions.
Nested settings use paths such as `settings["ansi_quotes"]`. Missing values use `<missing>`.
Values longer than 1024 JSON characters and differences beyond 32 entries carry explicit truncation notices.
Trusted paths and recovery instructions remain visible.
The warning excludes document text and unrelated response fields.
It retains `CUBRID-U1001`, warning severity, unsupported status, no coverage, rejection before parse, and owned-worker cleanup.
Malformed identities, test-only identities, manifest failures, and unavailable inputs retain their existing rejection rules and codes.

## Implementer verification

The new public-interface tests ran before production changes with this command:

```sh
PYTHONPATH=/home/vimkim/gh/cubrid-language-tools-native-identity/src /home/vimkim/gh/cubrid-language-tools/.venv/bin/python -m unittest discover -s tests -p test_native_identity.py -v
```

Five tests ran. Four assertions failed across the single-field SQL/CSQL case, multiple-field case, and CLI JSON case.
Each failure identified missing expected/actual details in the original generic warning.
Matching-identity and rejection-taxonomy controls passed.

After the change, all six diagnostic tests pass, including the added output-bound control.
They exercise `NativeWorker`, `Validator`, and the real CLI subprocess.
They verify nested missing/extra settings, deterministic order, escaped Unicode/quotes/newlines in paths and values, unchanged taxonomy, and a successful matching identity.
Request receipts prove no parse after rejection, no relaunch on repeated validation, and reaped worker PIDs.
The CLI retains exit 2, unsupported status, warning severity, and the detailed message in JSON.

All 165 default tests pass against a task-local installation and current source:

```sh
PYTHONPATH=/home/vimkim/gh/cubrid-language-tools-native-identity/src .venv/bin/python -m unittest discover -s tests -v
```

The log is `task-core-suite.log` under the evidence directory below.
The borrowed main `.venv` initially passed 164 of 165 tests.
Its stale installed metadata lacked the existing `cubrid-schema` entry point.
A fresh task-local installation resolves that environment mismatch without modifying the shared environment.

## Coordinator acceptance

Evidence is retained at `/home/vimkim/temp/cubrid-native-identity-20261031`.
The coordinator rebuilt ordered-v4 using the four pinned native README inputs and qualified 393 fixtures.
`qualification.log` reports no network, descendants, or external writable opens.
The installed native build directory contains the rebuilt worker and manifest together.
Both previous v3 directories remain preserved. All 16 qualified library/runtime asset hashes remain unchanged.
The installed server now returns `valid` with complete coverage for `SELECT 1;` and `CUBRID-S1001` for `SELECT ,;`.
The existing native suite passes 49 native tests and 20 adapter tests in `native-suite.log`.

The complete Neovim suite passes all 32 case receipts, including six native cases, in `nvim-current.log`.
Real headless Neovim 0.12.5 first failed because the old warning omitted `coverageRevision`, recorded in `editor-red.log`.
The task server then passed `run-editor-proof.sh`, recorded in `editor-green.log` and `nvim-warning-green/results.json`.
The editor diagnostic and diagnostic float retain the expected v4 revision, actual v3 revision, paths, and recovery advice.
The failed doctor probe retains the same details.
Switching to the rebuilt worker restores syntax diagnostics, clears them for valid SQL, provides SELECT completion, and passes the doctor probe.
The proof also verifies owned-server and worker cleanup.

## Limitations and delivery state

This ticket changes diagnostic text and documentation. It changes no grammar, coverage, trust settings, or runtime dependencies.
The coordinator repaired the local native installation without changing user configuration or Neovim source.
The new warning requires main integration and a server reinstall before the global installation uses it.
No merge, rebase, global Python installation, push, or publication is part of the implementer work.
