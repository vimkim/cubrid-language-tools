import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from cubrid_language.config import ConfigError, resolve_config
from cubrid_language.validation import PROFILE


class ConfigurationTests(unittest.TestCase):
    def test_default_profile_and_filename_mode_are_reusable_without_io_to_a_runtime(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for path, mode in (('job.csql', 'csql'), ('job.sql', 'sql'), (None, 'sql')):
                with self.subTest(path=path):
                    result = resolve_config(path, cwd=root)
                    self.assertEqual((result.profile, result.script_mode, result.schema_snapshot),
                                     (PROFILE, mode, None))

    def test_each_field_follows_flags_explicit_config_nearest_config_then_defaults(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            nested = root / 'nested'
            nested.mkdir()
            (root / '.cubrid-language.json').write_text(json.dumps({
                'profile': 'ancestor', 'scriptMode': 'csql', 'schemaSnapshot': 'old.json'}))
            nearest = nested / '.cubrid-language.json'
            nearest.write_text(json.dumps({'profile': 'nearest', 'schemaSnapshot': 'local.json'}))
            explicit_dir = root / 'settings'
            explicit_dir.mkdir()
            explicit = explicit_dir / 'chosen.json'
            explicit.write_text(json.dumps({'scriptMode': 'csql', 'schemaSnapshot': 'chosen.json'}))
            result = resolve_config('job.sql', cwd=nested, config_path=explicit)
            self.assertEqual((result.profile, result.script_mode, result.schema_snapshot),
                             ('nearest', 'csql', explicit_dir / 'chosen.json'))
            result = resolve_config('job.sql', cwd=nested, config_path=explicit,
                                    profile='flag', script_mode='sql', schema_snapshot='flag.json')
            self.assertEqual((result.profile, result.script_mode, result.schema_snapshot),
                             ('flag', 'sql', nested / 'flag.json'))
            result = resolve_config(None, cwd=nested, schema_snapshot=None)
            self.assertEqual((result.profile, result.script_mode, result.schema_snapshot),
                             ('nearest', 'sql', None))
            explicit.write_text('{"schemaSnapshot": null}')
            result = resolve_config('job.csql', cwd=nested, config_path=explicit)
            self.assertEqual((result.profile, result.script_mode, result.schema_snapshot),
                             ('nearest', 'csql', None))

    def test_invalid_or_untrusted_project_metadata_is_an_explicit_configuration_error(self):
        invalid = [[], None, 5, {'profile': ''}, {'profile': 11.5}, {'scriptMode': 'auto'},
                   {'schemaSnapshot': 5}, {'schemaSnapshot': ''}, {'profile': '\ud800'},
                   {'schemaSnapshot': '\u0000'}, {'parserWorker': '/tmp/worker'},
                   {'runtimePrefix': '/tmp/runtime'}, {'command': 'anything'},
                   {'password': 'secret'}, {'unknown': True}]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = root / '.cubrid-language.json'
            for value in invalid:
                with self.subTest(value=value):
                    config.write_text(json.dumps(value))
                    with self.assertRaises(ConfigError) as error:
                        resolve_config('job.sql', cwd=root)
                    self.assertEqual(error.exception.code, 'CUBRID-T1003')
            for wire in (b'not json', b'\xff', b'{"profile":"a","profile":"b"}'):
                with self.subTest(wire=wire):
                    config.write_bytes(wire)
                    with self.assertRaises(ConfigError):
                        resolve_config(None, cwd=root)
            config.unlink()
            with self.assertRaises(ConfigError):
                resolve_config(cwd=root, config_path='missing.json')

    def test_discovery_uses_each_document_parent_and_rejects_broken_configuration_links(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first, second = root / 'first', root / 'second'
            first.mkdir()
            second.mkdir()
            (first / '.cubrid-language.json').write_text('{"profile":"first"}')
            (second / '.cubrid-language.json').write_text('{"profile":"second"}')
            self.assertEqual(resolve_config('first/job.sql', cwd=root).profile, 'first')
            self.assertEqual(resolve_config('second/job.sql', cwd=root).profile, 'second')
            (root / '.cubrid-language.json').symlink_to('missing-config.json')
            with self.assertRaises(ConfigError):
                resolve_config(None, cwd=root)

    def test_permission_failure_during_discovery_cannot_fall_back_to_defaults(self):
        with patch('pathlib.Path.lstat', side_effect=PermissionError('configuration access denied')):
            with self.assertRaises(ConfigError) as error:
                resolve_config('job.sql', cwd='/explicit/project')
        self.assertEqual(error.exception.code, 'CUBRID-T1003')
        self.assertIn('configuration access denied', str(error.exception))

    def test_invalid_caller_overrides_and_deep_json_are_configuration_failures(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for override in ({'profile': ''}, {'profile': 5}, {'script_mode': 'auto'},
                             {'schema_snapshot': ''}, {'schema_snapshot': b'bytes'}):
                with self.subTest(override=override), self.assertRaises(ConfigError):
                    resolve_config(cwd=root, **override)
            (root / '.cubrid-language.json').write_text('[' * 2000 + ']' * 2000)
            with self.assertRaises(ConfigError):
                resolve_config(cwd=root)


if __name__ == '__main__':
    unittest.main()
