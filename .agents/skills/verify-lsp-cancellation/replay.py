"""Drive the real Adapter methods across the cleanup/queued-job race."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
import threading

from cubrid_language.lsp_server import Adapter, ValidationJob


def require(event, label):
    if not event.wait(5):
        raise RuntimeError(f'timed out waiting for {label}')


async def replay():
    adapter = Adapter(None)
    adapter.executor.shutdown()
    adapter.executor = ThreadPoolExecutor(max_workers=1)
    active_entered = threading.Event()
    release = threading.Event()
    queued_started = threading.Event()
    queued_validated = threading.Event()

    class Validator:
        def __init__(self, active):
            self.active = active

        def validate(self, *args):
            if self.active:
                active_entered.set()
                require(release, 'active cleanup')
            else:
                queued_validated.set()

        def close(self):
            if self.active:
                release.set()

    active, queued = ValidationJob(None), ValidationJob(None)
    active.validator, queued.validator = Validator(True), Validator(False)
    config = SimpleNamespace(profile='test', script_mode='sql')
    active_future = adapter.executor.submit(active.run, '', config)
    require(active_entered, 'active validation')

    def run_queued():
        try:
            return queued.run('', config)
        finally:
            queued_started.set()

    queued_future = adapter.executor.submit(run_queued)
    original = adapter.stop_job
    calls = 0
    early_cleanup = False

    def pause_after_first(job):
        nonlocal calls, early_cleanup
        if not all(item.cancelled.is_set() for item in (active, queued)):
            early_cleanup = True
        original(job)
        calls += 1
        if calls == 1:
            require(queued_started, 'queued job after cleanup freed slot')

    adapter.stop_job = pause_after_first
    try:
        adapter.stop_jobs([active, queued])
        active_future.result(timeout=5)
        queued_future.result(timeout=5)
        if adapter.cleanups:
            await asyncio.gather(*adapter.cleanups)
        if early_cleanup or queued_validated.is_set():
            raise AssertionError(
                f'cleanup submitted before all gates: {early_cleanup}; '
                f'queued validation entered after cleanup freed the slot before its gate: {queued_validated.is_set()}'
            )
        print('real-code replay: queued validation gated after cleanup freed the slot')
    finally:
        release.set()
        adapter.executor.shutdown(wait=True)


asyncio.run(replay())
