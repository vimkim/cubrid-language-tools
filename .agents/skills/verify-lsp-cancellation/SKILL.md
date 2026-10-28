---
name: verify-lsp-cancellation
description: Verify LSP bulk cancellation ordering when changing validation job gates, cleanup, configuration changes, or shutdown. Covers the cleanup-released queued-job race, not all LSP diagnostics or worker lifecycle behavior.
---

# Verify LSP bulk cancellation

Every job in a bulk cancellation batch must have its cancellation event set before any of that batch's cleanup is submitted. Otherwise cleanup can free a validation thread and let another queued batch member enter validation while still ungated.

From the repository root run:

```sh
python3 .agents/skills/verify-lsp-cancellation/run.py
```

The command uses `uv run --locked --extra lsp` for the real Python replay and Java for TLC 1.7.4. It downloads the pinned GitHub release to `${XDG_CACHE_HOME:-~/.cache}/cubrid-language-verification` on first use and checks SHA-256 on every run. It needs Python 3.10+, uv, and Java. An empty TLC cache requires network; uv may also need network to obtain the locked packages, build dependencies, or Python. It changes no product files. Both replay and TLC must pass. A timeout, dependency failure, or model-checker error is not a pass. Read every TLA+ result with `/statechart`; follow that skill's current instructions. Its command is intentionally not embedded here.

Model correspondence last checked at full commit `e4607ec60bd13f31b5aa4e9357f59013ee009ca5`. Directly modeled and replayed: `src/cubrid_language/lsp_server.py` `ValidationJob.run`, `Adapter.stop_job`, and `stop_jobs`. Context reviewed but not proven: `diagnose`, `shutdown`, `finish`, and the configuration-change handler in that file; `Validator.validate` and `close` in `src/cubrid_language/validation/service.py`; and `NativeWorker.close` and `_start` in `src/cubrid_language/validation/worker.py`. Compare these functions to that commit with `git diff` and inspect them before relying on a pass. The replay observes real adapter methods with deterministic validator doubles and executors; it does not model-check Python source. A passing replay or a source hash cannot prove model correspondence. If covered code changed, check each action and atomicity against it, update the model and replay as needed, replay a reachable broken schedule against a scratch copy of the real code, run this skill and `/statechart`, and only then advance the full sync commit. Use `/maintain-formal-verification-skill` when changes were not checked at the time.

`Cancellation.tla` starts with one active and two queued jobs, one validation slot, one ordered batch and separate validation and cleanup executors. `Gate` is one Event.set in `stop_jobs`; `Submit` is the call scheduling `Validator.close` via the independent executor; `Cleanup` combines cleanup's eventual release of the occupied slot with the active validation returning; `NaturalFinish` allows the active validation to finish independently. `CheckGate` is the Event.is_set read in `ValidationJob.run`, and `EnterValidate` is the later call to `Validator.validate`: cancellation can occur between them. `Done` is terminal stuttering. The model allows natural completion before the gate pass and permits a previously ungated job to enter validation after a later gate; neither is a violation of these properties. Submitted cleanup may run immediately. The model allows either queued job to take the slot, over-approximating the executor’s FIFO queue. One slot represents a chosen cleanup-released slot, not the production executor’s four slots; the bounded result does not establish the multi-slot case. The model omits task/future cancellation as an over-approximation of dispatch, unrelated jobs, multiple slots/batches, worker internals, diagnostics, and liveness. It assumes stable batch membership and event-loop ordering for the gate/submit loops. The finite result is not a proof for arbitrary batch sizes, scheduling, Python implementation details, or native processes.

`AllGatedBeforeCleanup` checks submission ordering. `NoCleanupReleasedUngatedValidation` checks the user-visible consequence: a queued member cannot enter validation after a cleanup-released slot while that member's gate was still unset at its read. A violation is a candidate bug: compare each step to real code and replay it before reporting; a failed replay may indicate a modeling error. Natural completion is not classified as cleanup release. Worker ownership is separate: `Validator.close` marks the validator closed under its ownership lock and closes an already-owned worker; `NativeWorker._start` checks `_closed` again under the process lock. These facts do not make the gate read and validation call atomic and do not prove that a previously passed gate cannot start a process.

To repeat the negative evidence without editing the checkout, run:

```sh
python3 .agents/skills/verify-lsp-cancellation/run.py --mutation-test
```

The command removes the initial gate loop only from a temporary source copy and requires the real replay to observe both early cleanup and queued validation. It also requires each model invariant to fail under `Broken = TRUE`. Interpret these model failures with `/statechart`, replay their paths, then run the baseline command again. A changed source that no longer matches the scratch mutation requires review; it is not a successful negative test.
