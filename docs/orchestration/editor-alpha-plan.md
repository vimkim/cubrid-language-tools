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
- [ ] Phase B: Design the workflow. Ground editor integration and compare two architecture sketches before dispatch.
- [ ] Phase C: Run the loop. Implement each independent consumer with public-interface TDD and real editor evidence.
- [ ] Phase D: Keep the audit trail. Record decisions and exact evidence as they occur.
- [ ] Phase E: Verify and hand back. Independently review packages and editor behavior before requesting integration.

## Throughput checkpoint

- [ ] Blocking first steps. Verify the engine/native baseline, choose editor lifecycle/configuration shapes, and prove a headless VS Code host can run before extension feature work.
- [ ] Independent workstreams. VS Code and Neovim own separate repositories, worktrees, tests, environments, and artifacts.
- [ ] Shared mutable state. The coordinator alone writes this plan, central tickets, common acceptance contracts, tracker state, and decision log. Workers read the core and qualified native artifacts.
- [ ] Smallest safe decomposition. One fresh implementation agent per editor ticket. Separate independent reviewers own bounded verification tasks after implementation.

## Proof and limits

Use the installed Neovim with its native LSP and a headless VS Code server/extension host driven by browser automation. Never launch desktop GUI programs or use forwarded X11.
Check installable artifacts, completion edits with Korean/emoji/CRLF, valid/syntax-error/unsupported native results, close cleanup, schema reload, and `.sql` opt-in.
Use the exact existing native worker and runtime as read-only trusted test inputs. A native parse baseline already returned valid, syntax-error and unsupported as expected.
Keep the core's accepted grammar/platform limits visible. Editor integration does not expand them.

## Architecture and arena checkpoints

- [x] Ground. Read the actual engine contract and current implementation.
- [ ] Sketch. Compare independent Astra and Terra packages.
- [ ] Agree. skip: default architect workflow proceeds after synthesis without a user checkpoint.
- [ ] Implement. Dispatch one fresh owner per consumer at exact commits.
- [ ] Scrap. skip: apply only if implementation demonstrates the selected shape is wrong.

- [x] Frame. Two consumer packages and a real-editor acceptance contract.
- [ ] Fan out. Independent candidate packages in `design-astra` and `design-terra`.
- [ ] Cross-judge. Read-only independent scoring after both packages finish.
- [ ] Pick. Score the whole designs against the consumer and maintainer criteria.
- [ ] Graft. Preserve useful evidence and remove unnecessary client policy.
- [ ] Verify. Confirm selected behavior against real editors before integration.

The real headless VS Code host prerequisite passed. OpenVSCode Server 1.109.5 ran a Node v22.21.1 extension host and a contributed command through headless Chromium. Evidence is `headless-host/result.json` and `headless-host/workbench.png` under the evidence directory. This proves the host, not the unfinished CUBRID extension.

## Durable records

- Architecture grounding and raw evidence live in `/home/vimkim/temp/cubrid-editor-alpha-aiYISe`.
- The canonical decision log is `docs/orchestration/editor-alpha-decisions.tsv` in this branch.
- VS Code consumer checkout is `/home/vimkim/gh/cubrid-vscode`.
- Neovim consumer checkout is `/home/vimkim/gh/cubrid.nvim`.
- Ticket definitions and exact dispatch commits will be recorded before fresh implementers start.
