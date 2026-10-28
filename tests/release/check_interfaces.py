"""Check installed public interfaces against portable, literal release fixtures."""

import argparse
from importlib import metadata
import json
from pathlib import Path
import subprocess
import sys
import tempfile

from cubrid_language import complete
from cubrid_language.validation import PROFILE, Validator, WorkerConfig


def check(worker, runtime, with_lsp):
    fixture = json.loads(Path(__file__).with_name('parity.json').read_text(encoding='utf-8'))
    console = Path(sys.executable).with_name('cubrid-lint')
    assert console.is_file(), console
    assert 'site-packages' in str(Path(__import__('cubrid_language').__file__)), 'requires an installed package'
    requirements = metadata.requires('cubrid-language-tools') or []
    assert all('extra == "lsp"' in item for item in requirements), requirements
    config = WorkerConfig(worker, runtime)
    client_type = None
    if with_lsp:
        import pygls  # Missing optional packages are qualification failures.
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'lsp'))
        from protocol_client import Client
        client_type = Client
    with tempfile.TemporaryDirectory() as directory:
        for case in fixture['validation']:
            selected = case.get('profile', PROFILE)
            actual_config = None if case.get('missingWorker') else config
            with Validator(actual_config) as validator:
                result = validator.validate(case['text'], selected, case['mode'])
            observed = [result.status, result.coverage, [d.code for d in result.diagnostics]]
            assert observed == case['expected'], (case['name'], observed)
            if 'spans' in case:
                assert [[d.span.start, d.span.end] for d in result.diagnostics] == case['spans'], case['name']
            command = [str(console), '--format', 'json', '--profile', selected,
                       '--script-mode', case['mode']]
            if actual_config:
                command += ['--parser-worker', str(worker), '--runtime-prefix', str(runtime)]
            reply = subprocess.run([*command, '-'], input=case['text'].encode('utf-8'),
                                   capture_output=True, cwd=directory, timeout=20)
            assert reply.returncode == case['exit'], (case['name'], reply.stderr)
            wire = json.loads(reply.stdout)
            assert wire['status'] == result.status and wire['offsetEncoding'] == 'unicode-codepoints'
            document = wire['documents'][0]
            assert {key: document[key] for key in result.to_dict()} == result.to_dict(), case['name']
            if client_type:
                settings = {'profile': selected, 'scriptMode': case['mode']}
                if actual_config:
                    settings.update(parserWorker=str(worker), runtimePrefix=str(runtime))
                with client_type(cwd=directory) as client:
                    client.initialize({'cubrid': settings})
                    uri = client.open(case['text'])
                    publication = client.diagnostics(uri, 1)
                    diagnostics = publication['diagnostics']
                    assert [d['code'] for d in diagnostics] == case['expected'][2], case['name']
                    assert [d['message'] for d in diagnostics] == [d.message for d in result.diagnostics]
                    assert [d['severity'] for d in diagnostics] == [1 if d.severity == 'error' else 2 for d in result.diagnostics]
                    assert [d['data'] for d in diagnostics] == [
                        {'category': d.category, 'rangePrecision': d.range_precision} for d in result.diagnostics]
                    if 'ranges' in case:
                        assert [d['range'] for d in diagnostics] == case['ranges'], case['name']
        for case in fixture['completion']:
            result = complete(case['text'], case['cursor'], PROFILE)
            assert result.allowed == case.get('allowed', True)
            assert [result.replacement.start, result.replacement.end] == case['span']
            assert [item.text for item in result.items] == case['items']
            if client_type:
                with client_type(cwd=directory) as client:
                    client.initialize()
                    uri = client.open(case['text'])
                    response = client.completion(uri, *case['position'])['result']['items']
                    assert [item['textEdit']['newText'] for item in response] == case['items']
                    assert all(item['textEdit']['range'] == case['range'] for item in response)
    print(json.dumps({'validationCases': len(fixture['validation']),
                      'completionCases': len(fixture['completion']), 'lsp': with_lsp,
                      'python': sys.version.split()[0]}, sort_keys=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker', type=Path, required=True)
    parser.add_argument('--runtime-prefix', type=Path, required=True)
    parser.add_argument('--lsp', action='store_true')
    args = parser.parse_args()
    check(args.worker.resolve(), args.runtime_prefix.resolve(), args.lsp)
