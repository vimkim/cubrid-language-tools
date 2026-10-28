#!/usr/bin/env python3
"""Run the baseline or replay the known broken variant in a temporary copy."""
import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import urllib.request

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DIGEST = '936a262061c914694dfd669a543be24573c45d5aa0ff20a8b96b23d01e050e88'
URL = 'https://github.com/tlaplus/tlaplus/releases/download/v1.7.4/tla2tools.jar'
parser = argparse.ArgumentParser()
parser.add_argument('--mutation-test', action='store_true', help='check a broken scratch copy and broken model')
args = parser.parse_args()
cache = Path(os.environ.get('XDG_CACHE_HOME', Path.home() / '.cache')) / 'cubrid-language-verification'
jar = cache / 'tla2tools-1.7.4.jar'
cache.mkdir(parents=True, exist_ok=True)
if not jar.exists():
    with urllib.request.urlopen(URL, timeout=60) as response:
        data = response.read()
    if hashlib.sha256(data).hexdigest() != DIGEST:
        raise SystemExit('TLC download checksum mismatch')
    with tempfile.NamedTemporaryFile(dir=cache, delete=False) as file:
        file.write(data)
        tmp = Path(file.name)
    tmp.replace(jar)
if hashlib.sha256(jar.read_bytes()).hexdigest() != DIGEST:
    raise SystemExit(f'TLC checksum mismatch: {jar}')
replay = ['uv', 'run', '--locked', '--extra', 'lsp', 'python', str(HERE / 'replay.py')]
with tempfile.TemporaryDirectory(prefix='lsp-cancellation-tlc-') as temp:
    scratch = Path(temp)
    if args.mutation_test:
        shutil.copytree(ROOT / 'src', scratch / 'src', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        source = scratch / 'src/cubrid_language/lsp_server.py'
        original = source.read_text()
        before = '''        # Gate every queued start before cleanup can free a validation thread.
        for job in jobs:
            job.cancelled.set()
        for job in jobs:
            self.stop_job(job)
'''
        after = '''        for job in jobs:
            self.stop_job(job)
'''
        if original.count(before) != 1:
            raise SystemExit('scratch mutation does not match source; update it after reviewing the code')
        source.write_text(original.replace(before, after))
        env = dict(os.environ, PYTHONPATH=str(scratch / 'src'))
        result = subprocess.run(replay, cwd=ROOT, env=env, text=True, capture_output=True)
        expected = ('cleanup submitted before all gates: True; queued validation entered after cleanup '
                    'freed the slot before its gate: True')
        if result.returncode == 0 or expected not in result.stderr:
            raise SystemExit(f'mutation replay did not show the expected violation:\n{result.stdout}{result.stderr}')
        print(f'real-code mutation caught: {expected}', flush=True)
        model = scratch / 'Cancellation.tla'
        shutil.copy2(HERE / 'Cancellation.tla', model)
        for invariant in ('AllGatedBeforeCleanup', 'NoCleanupReleasedUngatedValidation'):
            config = scratch / f'{invariant}.cfg'
            config.write_text(f'SPECIFICATION Spec\nCONSTANT Broken = TRUE\nINVARIANT {invariant}\n')
            result = subprocess.run(['java', '-XX:+UseParallelGC', '-cp', str(jar), 'tlc2.TLC', '-workers', '1',
                                     '-metadir', temp, '-config', str(config), str(model)],
                                    cwd=temp, text=True, capture_output=True)
            if result.returncode == 0 or f'Invariant {invariant} is violated' not in result.stdout:
                raise SystemExit(f'model mutation did not show {invariant}:\n{result.stdout}{result.stderr}')
            print(f'model mutation caught: {invariant}', flush=True)
    else:
        subprocess.run(replay, cwd=ROOT, check=True)
        subprocess.run(['java', '-XX:+UseParallelGC', '-cp', str(jar), 'tlc2.TLC', '-workers', '1',
                        '-metadir', temp, '-config', str(HERE / 'Cancellation.cfg'), str(HERE / 'Cancellation.tla')],
                       cwd=temp, check=True)
print('Compare covered source with the sync commit and inspect all model mappings; see SKILL.md.', flush=True)
