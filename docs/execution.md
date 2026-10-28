# Central implementation execution

The user accepted architecture A and authorized implementation and local task commits.
The revised central graph supersedes the old eleven-ticket csql-future graph.
Work item 572 tracks the independent engine. Consumer projects remain in the roadmap.

## Ticket execution

1. Read AGENTS.md, the specification, contracts, ticket, and exact dispatch record.
2. Use one new agent with no inherited conversation and one isolated worktree per ticket.
3. Verify the branch descends from the exact dispatch commit before edits.
4. Use TDD for new public behavior. Exercise the same interface that callers use.
5. Keep edits within ownership. Ask the coordinator to serialize shared packaging and recipe changes.
6. Run ticket checks and review the diff. Commit meaningful task files before review.
7. Write a criterion-by-criterion report with commands, counts, baseline, limitations, and unrelated dirt.

Retain an incomplete checkpoint when a criterion cannot pass.
A focused test pass does not replace native qualification or final review.
Do not reuse an implementer agent for another ticket.

## Integration and publication

Request user approval before integrating ticket branches into `implement/central-engine`.
Present committed results and checks so approval is concrete.
One approval can cover an explicitly named batch of ready ticket commits.
After approval, verify the destination is clean, rebase onto its current tip, check, and merge with `--ff-only`.
Use the authorized squash fallback only when needed.
Final integration into local main requires approval too.
The repository has no remote. Repository creation, publication, and deployment require explicit authorization.
Preserve original csql-future checkpoints and unrelated worktrees.

## Milestones

Report completed, remaining, and blocked work after each milestone.
Update `orchestration/state.json` and work item 572 with durable evidence before yielding.
Run a final standards/spec review after all central tickets pass.
Commit any fixes and verify before claiming completion.
