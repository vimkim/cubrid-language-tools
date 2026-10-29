# Editor alpha delivery report

## Result

Two separate local editor consumers are implemented, packaged, independently verified, and integrated into their local `main` branches. The original engine needed one protocol-boundary fix before real editor clients could initialize. That fix is integrated into the core's `main`. The user approved local integration, the existing core `origin/main` push and scoped task cleanup. Consumer publication remains a separate decision.

| Component | Integrated source | Evidence |
| --- | --- | --- |
| Shared LSP compatibility | `main` includes `3efe03b49a037041fe6e667acb990fc8403c3ab0`; source fix `d5a571eb03d543af1438b85933fcad3aed60f9f0` | 109 core tests, 30 LSP tests, captured real editor initialization, root framed repro, unchanged 143-state cancellation model |
| VS Code consumer | `main`, `c6b2aeaaf837f15d26298f925ca0ee23e1e2f2a2` | Installed VSIX, independent recovery and alpha runs, wire checks, native-worker cleanup, source/package correspondence |
| Neovim consumer | `main`, `4b4c4d9e486f0b02c146d21cb8452b3c45bad754` | Extracted artifact, real Ctrl-Y menu acceptance, independent foreign/mixed/owned menu checks, full editor suite, source/package correspondence |

The core's pre-integration baseline was `3bb70e492efe7bcb7de58a801281f7a088a9c39e`. Both consumer mains preserve the entire independently reviewed source trees. Neither consumer has a remote.

## User workflow

The VSIX registers `cubrid` and `.csql`, adds lexical highlighting and indentation, and uses one owned stdio language server per window. Generic `.sql` is opt-in through file associations. Trusted user or remote-machine settings choose executable paths. An untrusted workspace gets lexical support and no language-server process. Commands expose schema reload and explicit server restart.

The Neovim plugin uses built-in LSP, case-insensitive `.csql` detection, lexical highlighting, buffer-local indentation, trusted Lua setup, schema reload and restart commands. Generic `.sql` is opt-in. Its documented completion sequence is Ctrl-X Ctrl-O, Ctrl-N or Ctrl-P, then Ctrl-Y. The adapter applies the engine's full supported replacement span, including suffix text after the request cursor.

Both preserve schema availability and stale metadata reporting, complete settings replacement, native diagnostic codes, multi-project metadata and owned lifecycle. Neither executes SQL, connects to a database, downloads a native runtime, or duplicates the core completion/parser engine. The native inputs were read-only throughout.

## Installable artifacts

| Artifact | Path | SHA-256 |
| --- | --- | --- |
| VSIX | `/home/vimkim/temp/cubrid-editor-alpha-aiYISe/vscode-retirement/cubrid-language-0.1.0.vsix` | `621a757ddce1c33b7e9c624d312e66e4faddf21cbca11969720154f358b5f39b` |
| Neovim runtime archive | `/home/vimkim/temp/cubrid-editor-alpha-aiYISe/neovim-ownership/artifact/cubrid.nvim-final.tar.gz` | `94ea53e891e261693f1c1472cb8929cb8dbb3190fbb3c18ee55f110ef140f824` |

Initial candidate acceptance used `/home/vimkim/temp/cubrid-lsp-enums-venv/bin/cubrid-language-server`. Integration checks use the stable `/home/vimkim/gh/cubrid-language-tools/.venv/bin/cubrid-language-server`, reading the integrated main checkout. The old candidate environment now also points to that stable source, so retained harnesses do not depend on a removed worktree. The qualified native executable is `/home/vimkim/gh/cubrid-language-tools/native/parser-worker/build/parser-worker`; its runtime prefix is `/home/vimkim/.cub/install/develop/debug`.

The original core baseline rejects standard client enum fields. The fix is now integrated, and the stable main-checkout server passed real editor initialization and completion.

Local installation instructions are in the consumers' Korean and English READMEs:

- `/home/vimkim/gh/cubrid-vscode/README.md` and `README.en.md`.
- `/home/vimkim/gh/cubrid.nvim/README.md` and `README.en.md`.

These artifacts contain editor integration only. The separately installed Python server and qualified native runtime remain prerequisites. Keyword completion continues when the native runtime is unavailable, with a visible diagnostic.

## Problems found and corrected

1. Real Neovim and vscode-languageclient initialize requests exposed strict primitive hooks that rejected legal string/integer enum fields. The shared fix validates the exact wire primitive and constructs the authoritative lsprotocol enum. A failing framed regression was committed before the repair; malformed primitive and direct enum cases remain rejected.
2. Neovim's native plain-word completion retained the suffix after the cursor. A direct text-edit test had missed the normal menu behavior. The new private adapter owns request identity and acceptance context, uses public editor APIs, and deletes only the range-authorized remaining suffix after verified Ctrl-Y acceptance. The real menu regression failed with `SELECTect` before and passed with `SELECT` after.
3. Deferred Neovim cancellation could close a replacement provider's menu after filetype detach. The guard now verifies every displayed item belongs to the captured epoch/generation/choice before sending cancellation. The root's unchanged foreign-menu repro passes on the final artifact.
4. VS Code could not recover when an executable launched but never answered initialize. The session now owns the public-factory child, observes bounded startup and retirement, keeps the latest valid settings, and interrupts pending startup independently of reconciliation. No successor is admitted until the child, streams, start and editor feature registrations retire.

SDK 9.0.1 can reject disposal after removing old features. A successful disposal return was an incorrect proxy gate. Actual headless-host probes verified old registrations inactive and a healthy successor working in hanging, inherited-pipe and late-initialize cases. Known SDK rejections are classified only after those retirement postconditions. No private SDK cleanup or state mutation is used.

## Independent verification

Root independently reproduced the legal `trace: off` initialization failure before the core fix and acceptance afterward. The root review environment passed 109 core and 30 LSP tests. The unchanged cancellation verification exhausted 143 distinct states with both invariants satisfied; its three-job/one-slot scope does not expand because editor consumers were added.

The final VSIX independent review used fresh profiles and the actual OpenVSCode Server 1.109.5 Node extension host with headless Chromium. It passed 15 standard installed-host runs and three additional public-provider adversarial runs, including active old registrations, initialization racing termination, and inherited output pipes. All 325 archive members matched the clean source rebuild. The review observed all 27 recorded process IDs absent afterward. The earlier failed reviewer setup used missing remote-machine configuration, was retained as setup evidence, and was corrected through the public editor API.

The final Neovim independent review used the exact extracted archive and Neovim 0.12.5. The original foreign-menu and Ctrl-Y menu probes passed unchanged; separate old-owned cancellation, mixed-menu preservation and the full extracted suite passed. All 24 packaged files matched the clean source and behavior commit. Earlier independent adapter review also exercised unsupported/malformed responses, stale ordering and repeated accepted events. The newer-popup-before-old-callback ordering itself remains unverified; it is not counted as the passing overlap test.

Comment/suppression reviews found no deletion candidates or open flags in the reviewed source. No native source, generated headers, library/runtime inputs, database, daemon, consumer remote or user editor profile was changed.

After approval, rebases preserved all three reviewed source trees. Before merging, 109 core tests, 30 LSP tests, four VS Code unit tests and the full Neovim suite passed again. The coordinator's approved documentation diff was byte-identical after its rebase onto the core fix. A further installed VSIX full-host run and the unchanged original Neovim menu probe passed using the stable main-checkout server. The main-host wire check observed three shutdown/exit pairs and seven close events. Both recorded main-host process IDs were absent afterward. Receipts are in `/home/vimkim/temp/cubrid-editor-alpha-integration-9y5pl_7z`.

## Scope and remaining limits

- The tested VS Code-compatible host is OpenVSCode Server 1.109.5. Microsoft VS Code desktop and the declared 1.109.0 minimum were not exercised.
- Neovim 0.12.5 was exercised. Lower versions and other platforms remain unverified.
- Neovim's supported full-span acceptance key is Ctrl-Y. Space/Escape are native discard exits and may retain preview suffix text. Multiline edits, snippets, insert/replace edits, commands, additional edits and resolution-dependent items are visibly rejected. An unclosed quote at EOF can produce an unsupported multiline edit.
- Normal owned server/native-worker cleanup was observed. A direct forced kill does not establish arbitrary descendant cleanup. Complete VS Code window/host shutdown ordering remains outside the tested deactivation and restart paths.
- Native syntax qualification remains the exact Linux x86-64 V3 CUBRID profile and its existing grammar limits. This work adds no semantic analysis or formatting.
- The original core also accepts an empty capabilities array and permissive values in an enum-or-integer union. These pre-existing boundary-validation cases remain a separate follow-up. Unknown numeric values in open integer unions need protocol interpretation before any stricter policy.
- Both consumer repositories and all artifacts are local. No marketplace, package-index, GitHub repository creation, consumer push or deployment occurred.

## Approved integration

The coordinator work was prepared on `editor/alpha`. It owns planning, contracts, decision trail, state, this report and user-facing delivery status documentation. These records belong to the central repository.

The user approved the concrete integration proposal with "nice. yes". Each destination was checked clean and on `main`; the core fix and both final consumer branches were merged with `--ff-only`. The coordinator was rebased onto the integrated core fix without changing its approved documentation patch. The integrated core was pushed to `origin/main` at `8f75acd66e3691d635a14c8b5c7ca918917d0d74` before the final audit record. The final published SHA is recorded in work item582 and `final.json` in the integration evidence directory. Consumer publication is separate because those repositories have no configured remotes.

Only verified merged task worktrees/branches are eligible for removal without force. Final artifacts, raw receipts and source correspondence remain in `/home/vimkim/temp/cubrid-editor-alpha-aiYISe`. Integration receipts and preserved task reports are in `/home/vimkim/temp/cubrid-editor-alpha-integration-9y5pl_7z`. The final remote SHA and cleanup outcome are recorded in work item 582. Valuable native inputs and original csql-future checkpoints remain untouched.

## Evidence index

Paths below are relative to `/home/vimkim/temp/cubrid-editor-alpha-aiYISe`:

- `native-baseline.json`, `core-initialize-red.json`, `core-initialize-green.json`, and `core-independent/{core.log,lsp.log,formal.log}`.
- `headless-host/RECEIPT.md`, `grounding.md`, architecture sketches and verdicts, and the startup retirement SDK receipts.
- `vscode-retirement-independent/report.md`, `vscode-retirement/sdk4/result.json`, final host case receipts, and the final VSIX.
- `neovim-final-independent/report.md`, `neovim-menu-independent/report.md`, root menu observations, final ownership receipts, and the final archive.
- `comment-review-neovim-core.md`, `comment-review-vscode.md`, `comment-review-menu.md`, and `comment-review-final.md`.

The canonical append-only decision trail is `docs/orchestration/editor-alpha-decisions.tsv`. Exact worktree/branch/commit and artifact state is in `docs/orchestration/editor-alpha-state.json`.

The independent `gpt-6-astra` trail audit passed after five append-only corrections. It reviewed all 21 frozen rows against the scoped session and supporting files. Two rows add omitted repair design choices; three supersede incomplete evidence pointers without changing the supported outcomes. No unresolved trail flags remain. The audit report is `/home/vimkim/temp/cubrid-editor-alpha-aiYISe/audit/report.md`; `corrected-scope.json` records the frozen log and transcript hashes. This was independent agent judgment using the available GPT models, without cross-provider review. The product limits above remain unchanged by the audit.

The integration trail audit also passed. It checked rows 23 through 29 against the full approval-turn transcript, rebase and merge receipts, test logs, live remote comparison and seven completed worktree removals. No corrective row was required. Its report is `/home/vimkim/temp/cubrid-editor-alpha-integration-9y5pl_7z/audit/report.md`. The final audit-record push and coordinator cleanup follow the same approval and are recorded in the final receipt and work item582.
