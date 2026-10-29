"""Core-only installations must remain independent of optional adapter packages."""

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


class BootstrapTests(unittest.TestCase):
    def run_launcher(self, arguments, version=None):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = Path(__file__).resolve().parents[1] / 'src' / 'cubrid_language'
            shutil.copytree(source, root / 'cubrid_language', ignore=shutil.ignore_patterns('__pycache__'))
            if version is not None:
                metadata = root / 'cubrid_language_tools-9.8.7.dist-info'
                metadata.mkdir()
                (metadata / 'METADATA').write_text(
                    f'Metadata-Version: 2.1\nName: cubrid-language-tools\nVersion: {version}\n', encoding='utf-8')
            environment = dict(os.environ)
            environment['PYTHONPATH'] = str(root)
            return subprocess.run([sys.executable, '-S', '-m', 'cubrid_language.lsp', *arguments],
                cwd=root, capture_output=True, env=environment, timeout=5)

    def test_version_reads_installed_metadata_without_optional_dependencies(self):
        result = self.run_launcher(['--version'], version='9.8.7')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, b'cubrid-language-server 9.8.7\n')
        self.assertEqual(result.stderr, b'')

    def test_version_without_metadata_reports_installation_guidance(self):
        result = self.run_launcher(['--version'])
        self.assertEqual(result.returncode, 3)
        self.assertEqual(result.stdout, b'')
        self.assertIn(b'cubrid-language-tools', result.stderr)
        self.assertIn(b'install', result.stderr.lower())
        self.assertNotIn(b'Traceback', result.stderr)

    def test_help_without_optional_dependencies_or_metadata(self):
        for flag in ('--help', '-h'):
            with self.subTest(flag=flag):
                result = self.run_launcher([flag])
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stderr, b'')
                for text in (b'cubrid-language-server', b'--version', b'--help', b'-h'):
                    self.assertIn(text, result.stdout)

    def test_invalid_arguments_fail_without_stdout(self):
        for arguments in (['--unknown'], ['--ver'], ['--version', '--help'],
                          ['--version', '--version'], ['--help', '-h'],
                          ['--version', 'extra'], ['extra']):
            with self.subTest(arguments=arguments):
                result = self.run_launcher(arguments, version='9.8.7')
                self.assertEqual(result.returncode, 3)
                self.assertEqual(result.stdout, b'')
                self.assertIn(b'--help', result.stderr)

    def test_missing_optional_dependencies_print_guidance_only_on_stderr(self):
        environment = dict(os.environ)
        environment['PYTHONPATH'] = str(Path(__file__).resolve().parents[1] / 'src')
        result = subprocess.run([sys.executable, '-S', '-m', 'cubrid_language.lsp'],
            capture_output=True, env=environment, timeout=5)
        self.assertEqual(result.returncode, 3)
        self.assertEqual(result.stdout, b'')
        self.assertIn(b'cubrid-language-tools[lsp]', result.stderr)

    def test_core_and_bootstrap_import_without_optional_dependencies(self):
        environment = dict(os.environ)
        environment['PYTHONPATH'] = str(Path(__file__).resolve().parents[1] / 'src')
        result = subprocess.run([sys.executable, '-S', '-c',
            'import cubrid_language, cubrid_language.cli, cubrid_language.lsp; import sys; '
            'assert not any(m in sys.modules for m in ("pygls", "lsprotocol", "cattrs", "attrs"))'],
            capture_output=True, env=environment, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)
