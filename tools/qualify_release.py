"""Build and qualify local archives in isolated Python 3.10 and 3.14 installs.

Requires uv and an already built, qualified V3 worker. No runtime download,
database, daemon, destination merge, or publication is performed.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tarfile

from check_artifacts import check


def qualify(root, build, output):
    output.mkdir(parents=True, exist_ok=False)
    environment = dict(os.environ)
    environment.pop('PYTHONPATH', None)
    environment['UV_PYTHON_DOWNLOADS'] = 'never'
    environment['UV_LINK_MODE'] = 'copy'
    records = []

    def run(name, command, cwd=output, expected=0):
        log = output / (name + '.log')
        with log.open('wb') as stream:
            result = subprocess.run(list(map(str, command)), cwd=cwd, env=environment,
                                    stdin=subprocess.DEVNULL, stdout=stream, stderr=subprocess.STDOUT,
                                    timeout=600)
        records.append({'name': name, 'argv': list(map(str, command)), 'cwd': str(cwd),
                        'exit': result.returncode, 'logSha256': hashlib.sha256(log.read_bytes()).hexdigest()})
        (output / 'commands.json').write_text(json.dumps(records, indent=2) + '\n')
        assert result.returncode == expected, (name, result.returncode, log)
        print(name, 'passed', flush=True)

    manifest = json.loads((build / 'manifest.json').read_bytes())
    assert manifest['coverageRevision'] == 'bounded-query-dml-schema-engineer-v3'
    assert (build / 'parser-worker').is_file()
    runtime = manifest['runtimePrefix']
    constraints = output / 'build-constraints.txt'
    constraints.write_text('setuptools==77.0.3\n')
    for version in ('3.10', '3.14'):
        label = version.replace('.', '')
        artifacts = output / ('dist-' + label)
        run(label + '-build-minimum', ['uv', 'build', '--python', version, '--build-constraints',
                                     constraints, '--out-dir', artifacts, root])
        wheel = next(artifacts.glob('*.whl'))
        sdist = next(artifacts.glob('*.tar.gz'))
        check(root, wheel, sdist)
        extraction = output / ('source-' + label)
        extraction.mkdir()
        with tarfile.open(sdist) as archive:
            archive.extractall(extraction)
        source = next(extraction.iterdir())
        for form in ('wheel', 'source'):
            for extra in ('core', 'lsp'):
                name = label + '-' + form + '-' + extra
                venv = output / name
                python = venv / 'bin/python'
                run(name + '-venv', ['uv', 'venv', '--python', version, venv])
                target = wheel if form == 'wheel' else source
                install = ['uv', 'pip', 'install', '--python', python, '--build-constraints', constraints]
                install += [str(target) + '[lsp]'] if extra == 'lsp' else ['--no-deps', target]
                run(name + '-install', install)
                run(name + '-interfaces', [python, '-I', source / 'tests/release/check_interfaces.py',
                                          '--worker', build / 'parser-worker', '--runtime-prefix', runtime,
                                          *(['--lsp'] if extra == 'lsp' else [])])
                if extra == 'core':
                    run(name + '-default', [python, '-I', '-m', 'unittest', 'discover', '-s', source / 'tests', '-v'])
                    run(name + '-missing-extra', [venv / 'bin/cubrid-language-server'], expected=3)
                    assert '[lsp]' in (output / (name + '-missing-extra.log')).read_text()
                    run(name + '-inventory', [python, '-I', '-c',
                        "from importlib.metadata import distributions; assert {d.metadata['Name'] for d in distributions()} == {'cubrid-language-tools'}"])
                else:
                    run(name + '-framed', [python, '-I', '-m', 'unittest', 'discover', '-s', source / 'tests/lsp', '-v'])
                    run(name + '-pins', [python, '-I', '-c',
                        "import sys; from importlib.metadata import version; expected={'pygls':'2.1.1','lsprotocol':'2025.0.0','attrs':'25.4.0','cattrs':'25.3.0','typing-extensions':'4.15.0'}; expected.update({'exceptiongroup':'1.3.1'} if sys.version_info < (3,11) else {}); assert all(version(k)==v for k,v in expected.items())"])
    print('Release qualification passed. Commands and log hashes:', output / 'commands.json')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True, help='new directory for retained evidence')
    args = parser.parse_args()
    qualify(args.root.resolve(), args.build.resolve(), args.output.resolve())
