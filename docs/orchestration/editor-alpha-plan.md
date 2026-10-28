# Deliver the editor alpha

Work item 582 continues the completed central engine in work item 572.
The user selected VS Code and Neovim as the next usable milestone.
Core baseline is `3bb70e492efe7bcb7de58a801281f7a088a9c39e`.

## Definition of done

Both separate consumer projects have locally installable artifacts and committed, independently reviewed source.
A real headless editor opens `.csql` as `cubrid`, shows lexical highlighting and indentation, requests shared completion, and receives qualified native syntax diagnostics.
Both consumers preserve UTF-16 positions, full-document synchronization, configuration replacement, missing-runtime completion, schema reload, and owned process shutdown.
Generic `.sql` documents keep their editor default unless the user opts in.
Executable settings come from explicit trusted editor configuration, never project metadata or shell expansion.
No submitted SQL is executed.

The deliverable is a local alpha. Creating remote consumer repositories, publishing packages, or deploying is a separate authorization.
Integration follows the user's existing approval rule after concrete results are reviewable.

## Workflow

- [x] Read the Principles section of poteto-mode.
- [x] Phase A: Frame. Confirm core delivery, user milestone, tools, and native baseline.
- [x] Phase B: Design the workflow. Ground editor integration and compare two architecture sketches before dispatch.
- [x] Phase C: Run the loop. Implement each independent consumer with public-interface TDD and real editor evidence.
- [ ] Phase D: Keep the audit trail. Record decisions and exact evidence as they occur.
- [ ] Phase E: Verify and hand back. Independently review packages and editor behavior before requesting integration.

## Throughput checkpoint

- [x] Blocking first steps. Verify the engine/native baseline, choose editor lifecycle/configuration shapes, and prove a headless VS Code host can run before extension feature work.
- [x] Independent workstreams. VS Code and Neovim own separate repositories, worktrees, tests, environments, and artifacts.
- [x] Shared mutable state. The coordinator alone writes this plan, central tickets, common acceptance contracts, tracker state, and decision log. Workers read the core and qualified native artifacts.
- [x] Smallest safe decomposition. One fresh implementation agent per editor ticket. Separate independent reviewers own bounded verification tasks after implementation.

## Proof and limits

Use the installed Neovim with its native LSP and a headless VS Code server/extension host driven by browser automation. Never launch desktop GUI programs or use forwarded X11.
Check installable artifacts, completion edits with Korean/emoji/CRLF, valid/syntax-error/unsupported native results, close cleanup, schema reload, and `.sql` opt-in.
Use the exact existing native worker and runtime as read-only trusted test inputs. A native parse baseline already returned valid, syntax-error and unsupported as expected.
Keep the core's accepted grammar/platform limits visible. Editor integration does not expand them.

## Architecture and arena checkpoints

- [x] Ground. Read the actual engine contract and current implementation.
- [x] Sketch. Compare Terra's two structural alternatives and Astra's partial notes. The Astra runner did not complete a package.
- [x] Agree. skip: default architect workflow proceeds after synthesis without a user checkpoint.
- [x] Implement. Dispatch one fresh owner per consumer at exact commits.
- [x] Scrap. skip: apply only if implementation demonstrates the selected shape is wrong.

- [x] Frame. Two consumer packages and a real-editor acceptance contract.
- [x] Fan out. Independent candidate packages in `design-astra` and `design-terra`.
- [x] Cross-judge. Read-only independent scoring of the completed package with the other runner's dropout recorded.
- [x] Pick. Score the whole designs against the consumer and maintainer criteria.
- [x] Graft. Preserve useful evidence and remove unnecessary client policy.
- [x] Verify. Confirm selected behavior against real editors before integration.

The real headless VS Code host prerequisite passed. OpenVSCode Server 1.109.5 ran a Node v22.21.1 extension host and a contributed command through headless Chromium. Evidence is `headless-host/result.json` and `headless-host/workbench.png` under the evidence directory. This proves the host, not the unfinished CUBRID extension.

## Durable records

- Architecture grounding and raw evidence live in `/home/vimkim/temp/cubrid-editor-alpha-aiYISe`.
- The canonical decision log is `docs/orchestration/editor-alpha-decisions.tsv` in this branch.
- VS Code consumer checkout is `/home/vimkim/gh/cubrid-vscode`.
- Neovim consumer checkout is `/home/vimkim/gh/cubrid.nvim`.
- Ticket definitions and exact dispatch commits will be recorded before fresh implementers start.

The selected architecture is recorded in `editor-alpha-design.md`. The independent judge selected the instance session after correcting untitled metadata and CRLF expectations. One runner completed a package containing both structural alternatives; the other returned only partial notes and was stopped. Fresh implementation owners have exact dispatch commits in `editor-alpha-state.json`.

All independent product checks passed on the final artifacts. Core109/LSP30 and the unchanged143-state cancellation check pass. Final source/artifact commits and precise limits are in `editor-alpha-state.json` and `docs/tickets/reports/editor-alpha.md`. The decision-trail audit and explicit integration gate remain.
