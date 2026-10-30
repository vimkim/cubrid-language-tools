"""Fail if built release archives lose source, notice, or dependency contracts."""

import argparse
from email.parser import BytesParser
import hashlib
from pathlib import Path
import tarfile
import zipfile


def check(root, wheel, sdist):
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        info = next(name.rsplit('/', 1)[0] for name in names if name.endswith('.dist-info/METADATA'))
        metadata = BytesParser().parsebytes(archive.read(info + '/METADATA'))
        assert metadata['License-Expression'] == 'Apache-2.0', metadata['License-Expression']
        assert len(metadata.get_all('License-File', [])) == 19
        requirements = metadata.get_all('Requires-Dist', [])
        assert len(requirements) == 6 and all('extra == "lsp"' in value for value in requirements), requirements
        entry_points = archive.read(info + '/entry_points.txt').decode()
        assert 'cubrid-lint = cubrid_language.cli:main' in entry_points
        assert 'cubrid-schema = cubrid_language.schema_cli:main' in entry_points
        assert 'cubrid-language-server = cubrid_language.lsp:main' in entry_points
        modules = list((root / 'src/cubrid_language').rglob('*.py'))
        for path in modules:
            assert archive.read(path.relative_to(root / 'src').as_posix()) == path.read_bytes(), path
        notices = [root / 'LICENSE', *(root / 'native/parser-worker/notices').glob('*.txt'),
                   root / 'native/parser-worker/notices/README.md']
        for path in notices:
            assert archive.read(info + '/licenses/' + path.relative_to(root).as_posix()) == path.read_bytes(), path
        assert not any(name.endswith(('.so', '.o', '.a', '/parser-worker')) for name in names)
    with tarfile.open(sdist) as archive:
        members = {item.name: item for item in archive.getmembers()}
        prefix = next(iter(members)).split('/')[0] + '/'
        sources = [path for folder in ('src/cubrid_language', 'native/parser-worker', 'tests', 'docs', 'tools', 'assets')
                   for path in (root / folder).rglob('*') if path.is_file()
                   and not any(part in ('build', '__pycache__') for part in path.relative_to(root).parts)
                   and path.suffix in ('.py', '.cpp', '.hpp', '.md', '.txt', '.json', '.strace', '.svg', '.html')]
        for path in [*sources, root / 'README.en.md', root / 'justfile', root / 'uv.lock', root / 'LICENSE']:
            name = prefix + path.relative_to(root).as_posix()
            assert name in members, name
            assert archive.extractfile(name).read() == path.read_bytes(), name
        assert not any('/native/parser-worker/build/' in name or name.endswith(('.so', '.o', '.a', '/parser-worker')) for name, member in members.items() if member.isfile())
    print('Checked', len(modules), 'package modules,', len(notices), 'license files,', len(sources), 'source files, all three commands and six optional-only requirements')
    for path in (wheel, sdist):
        print(path.name, hashlib.sha256(path.read_bytes()).hexdigest())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--wheel', type=Path, required=True)
    parser.add_argument('--sdist', type=Path, required=True)
    args = parser.parse_args()
    check(args.root.resolve(), args.wheel, args.sdist)
