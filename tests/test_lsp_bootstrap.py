"""Core-only installations must remain independent of optional adapter packages."""

import os
from pathlib import Path
import subprocess
import sys
import unittest


class BootstrapTests(unittest.TestCase):
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
