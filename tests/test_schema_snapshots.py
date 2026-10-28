"""Offline snapshot behavior exercised through shared public interfaces."""

from contextlib import ExitStack
from copy import deepcopy
from dataclasses import FrozenInstanceError
import io
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from cubrid_language import Relation, Schema, complete
from cubrid_language.schema import load_snapshot, refresh_snapshot


PROFILE = 'cubrid-11.5.0.2704-cc94778'


class SchemaSnapshotTest(unittest.TestCase):

  def setUp(self):
    directory = TemporaryDirectory()
    self.addCleanup(directory.cleanup)
    self.path = Path(directory.name) / 'schema.json'

  def write_snapshot(self, data):
    self.path.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')

  def test_no_configured_snapshot_keeps_keyword_completion_available(self):
    snapshot = load_snapshot(None)
    self.assertIsNone(snapshot.schema)
    self.assertFalse(snapshot.stale)
    self.assertIn('not configured', snapshot.availability)
    self.assertEqual(['SELECT'], [item.text for item in
                                 complete('sel', 3, PROFILE, snapshot.schema).items])
    text = 'select * from co'
    self.assertEqual((), complete(text, len(text), PROFILE, snapshot.schema).items)

  def test_missing_snapshot_reports_initial_unavailability(self):
    snapshot = load_snapshot(self.path)
    self.assertIsNone(snapshot.schema)
    self.assertFalse(snapshot.stale)
    self.assertIn('unavailable', snapshot.availability)
    self.assertIn(str(self.path), snapshot.availability)

  def test_valid_metadata_preserves_unicode_and_drives_completion(self):
    self.write_snapshot({
      'schemaVersion': 1,
      'user': '사용자',
      'relations': [
        {'owner': '사용자', 'name': '고객', 'kind': 'CLASS', 'columns': ['번호', '이름']},
        {'owner': 'PUBLIC', 'name': '고객 목록', 'kind': 'VCLASS', 'columns': ['고객 이름']},
      ],
    })
    snapshot = load_snapshot(self.path)
    self.assertIsNone(snapshot.availability)
    self.assertFalse(snapshot.stale)
    self.assertEqual(Schema('사용자', (
      Relation('사용자', '고객', 'CLASS', ('번호', '이름')),
      Relation('PUBLIC', '고객 목록', 'VCLASS', ('고객 이름',)),
    )), snapshot.schema)
    text = 'select * from 고'
    self.assertEqual(['[고객 목록]', '고객'], [item.text for item in
                                         complete(text, len(text), PROFILE, snapshot.schema).items])
    text = 'select 고.이 from 고객 고'
    self.assertEqual(['이름'], [item.text for item in
                             complete(text, len('select 고.이'), PROFILE, snapshot.schema).items])

  def test_schema_version_must_be_integer_one(self):
    for version in (None, True, False, 1.0, '1', 0, 2):
      with self.subTest(version=version):
        self.write_snapshot({'schemaVersion': version, 'user': 'reader', 'relations': []})
        snapshot = load_snapshot(self.path)
        self.assertIsNone(snapshot.schema)
        self.assertFalse(snapshot.stale)
        self.assertIn('schemaVersion', snapshot.availability)

  def test_invalid_required_metadata_rejects_the_entire_snapshot(self):
    valid = {
      'schemaVersion': 1, 'user': 'reader',
      'relations': [{'owner': 'reader', 'name': 'code', 'kind': 'CLASS', 'columns': ['id']}],
    }
    invalid = [('snapshot', value) for value in (None, [], 'metadata', 1)]
    for field in ('schemaVersion', 'user', 'relations'):
      value = deepcopy(valid)
      del value[field]
      invalid.append((field, value))
    for field, replacement in (('user', None), ('user', 1), ('user', []),
                               ('relations', None), ('relations', {}), ('relations', 'code')):
      value = deepcopy(valid)
      value[field] = replacement
      invalid.append((field, value))
    for replacement in (None, [], 'code', 1):
      value = deepcopy(valid)
      value['relations'] = [replacement]
      invalid.append(('relations[0]', value))
    for field in ('owner', 'name', 'kind', 'columns'):
      value = deepcopy(valid)
      del value['relations'][0][field]
      invalid.append((f'relations[0].{field}', value))
    for field, replacement in (
      ('owner', None), ('owner', 1), ('name', []), ('name', False),
      ('kind', 1), ('kind', 'VIEW'), ('kind', 'class'),
      ('columns', None), ('columns', 'id'), ('columns', {}),
      ('columns', ['id', 3]), ('columns', ['id', None]),
    ):
      value = deepcopy(valid)
      value['relations'][0][field] = replacement
      invalid.append((f'relations[0].{field}', value))
    # A valid first relation cannot turn a partially invalid snapshot into a success.
    value = deepcopy(valid)
    value['relations'].append({'owner': 'reader', 'name': 'broken', 'kind': 'CLASS'})
    invalid.append(('relations[1].columns', value))
    for field, data in invalid:
      with self.subTest(field=field, data=data):
        self.write_snapshot(data)
        snapshot = load_snapshot(self.path)
        self.assertIsNone(snapshot.schema)
        self.assertFalse(snapshot.stale)
        self.assertIn('unavailable', snapshot.availability)
        self.assertIn(field, snapshot.availability)

  def test_optional_metadata_is_retained_immutably_and_unknown_fields_are_ignored(self):
    self.write_snapshot({
      'schemaVersion': 1, 'user': 'Reader', 'users': ['DBA', 'Reader', '😀 관리자'],
      'database': 'DemoDb', 'future': {'ignored': True},
      'relations': [
        {'owner': 'Reader', 'name': 'Code', 'kind': 'CLASS', 'columns': ['ID', 'Name'],
         'system': False, 'indexes': ['Idx_Name', '고객 인덱스'], 'future': [1, 2]},
        {'owner': 'DBA', 'name': 'db_class', 'kind': 'VCLASS', 'columns': ['class_name'],
         'system': True, 'indexes': []},
      ],
    })
    snapshot = load_snapshot(str(self.path))
    self.assertEqual(Schema('Reader', (
      Relation('Reader', 'Code', 'CLASS', ('ID', 'Name'), False, ('Idx_Name', '고객 인덱스')),
      Relation('DBA', 'db_class', 'VCLASS', ('class_name',), True),
    ), ('DBA', 'Reader', '😀 관리자'), 'DemoDb'), snapshot.schema)
    self.assertIsNone(snapshot.availability)
    with self.assertRaises(FrozenInstanceError):
      snapshot.stale = True
    for text, expected in (
      ('SHOW GRANTS FOR Re', ['Reader']),
      ('SHOW TABLES WHERE tab', ['tables_in_DemoDb']),
      ('SHOW INDEX HEADER OF Code.Idx', ['Idx_Name']),
      ('select * from db_cl', ['db_class']),
    ):
      with self.subTest(text=text):
        self.assertEqual(expected, [item.text for item in
                                    complete(text, len(text), PROFILE, snapshot.schema).items])

  def test_invalid_optional_metadata_rejects_the_snapshot(self):
    for field, replacement in (
      ('users', None), ('users', 'reader'), ('users', {}), ('users', ['reader', 1]),
      ('database', None), ('database', 7), ('database', []),
      ('system', None), ('system', 0), ('system', 1), ('system', 'false'),
      ('indexes', None), ('indexes', 'idx_name'), ('indexes', {}), ('indexes', ['idx_name', 1]),
    ):
      with self.subTest(field=field, replacement=replacement):
        data = {
          'schemaVersion': 1, 'user': 'reader',
          'relations': [{'owner': 'reader', 'name': 'code', 'kind': 'CLASS', 'columns': []}],
        }
        if field in ('users', 'database'):
          data[field] = replacement
        else:
          data['relations'][0][field] = replacement
        self.write_snapshot(data)
        snapshot = load_snapshot(self.path)
        self.assertIsNone(snapshot.schema)
        self.assertFalse(snapshot.stale)
        self.assertIn(field, snapshot.availability)

  def test_failed_refresh_retains_last_valid_schema_and_completion_with_a_stale_message(self):
    self.write_snapshot({
      'schemaVersion': 1, 'user': 'reader',
      'relations': [{'owner': 'reader', 'name': 'Code', 'kind': 'CLASS', 'columns': ['Name']}],
    })
    initial = load_snapshot(self.path)
    previous = initial
    for data in (None, b'not JSON', b'\xff', b'{"schemaVersion": true, "user": "reader", "relations": []}'):
      with self.subTest(data=data):
        if data is None:
          self.path.unlink()
        else:
          self.path.write_bytes(data)
        current = refresh_snapshot(self.path, previous)
        self.assertEqual(initial.schema, current.schema)
        self.assertTrue(current.stale)
        self.assertIn('stale', current.availability)
        self.assertIn('retaining', current.availability)
        self.assertIn(str(self.path), current.availability)
        text = 'select * from Co'
        self.assertEqual(['Code'], [item.text for item in
                                   complete(text, len(text), PROFILE, current.schema).items])
        previous = current
    self.assertFalse(initial.stale)
    self.assertIsNone(initial.availability)

  def test_invalid_json_and_encoding_report_initial_unavailability(self):
    for data in (b'', b'{"schemaVersion": 1', b'{} trailing text', b'\xff', b'[' * 2000 + b']' * 2000):
      with self.subTest(data=data[:24]):
        self.path.write_bytes(data)
        snapshot = load_snapshot(self.path)
        self.assertIsNone(snapshot.schema)
        self.assertFalse(snapshot.stale)
        self.assertIn('unavailable', snapshot.availability)
        self.assertIn(str(self.path), snapshot.availability)

  def test_changed_metadata_is_used_only_after_explicit_refresh(self):
    self.write_snapshot({
      'schemaVersion': 1, 'user': 'reader',
      'relations': [{'owner': 'reader', 'name': 'Code', 'kind': 'CLASS', 'columns': ['OldName']}],
    })
    initial = load_snapshot(self.path)
    self.write_snapshot({
      'schemaVersion': 1, 'user': 'reader',
      'relations': [{'owner': 'reader', 'name': 'Customer', 'kind': 'VCLASS', 'columns': ['NewName']}],
    })
    text = 'select * from C'
    self.assertEqual(['Code'], [item.text for item in
                               complete(text, len(text), PROFILE, initial.schema).items])
    current = refresh_snapshot(self.path, initial)
    self.assertFalse(current.stale)
    self.assertIsNone(current.availability)
    self.assertEqual(['Customer'], [item.text for item in
                                   complete(text, len(text), PROFILE, current.schema).items])
    text = 'select c.Ne from Customer c'
    self.assertEqual(['NewName'], [item.text for item in
                                  complete(text, len('select c.Ne'), PROFILE, current.schema).items])
    self.assertEqual('Code', initial.schema.relations[0].name)

  def test_successful_refresh_recovers_from_stale_and_initially_unavailable_states(self):
    initial = load_snapshot(self.path)
    failed = refresh_snapshot(self.path, initial)
    self.assertIsNone(failed.schema)
    self.assertFalse(failed.stale)
    self.assertIn('unavailable', failed.availability)
    self.write_snapshot({'schemaVersion': 1, 'user': 'Reader', 'relations': [], 'users': ['Reader']})
    valid = refresh_snapshot(self.path, failed)
    self.assertEqual(('Reader',), valid.schema.users)
    self.path.unlink()
    stale = refresh_snapshot(self.path, valid)
    self.assertTrue(stale.stale)
    self.write_snapshot({'schemaVersion': 1, 'user': 'NewReader', 'relations': [], 'users': ['NewReader']})
    recovered = refresh_snapshot(self.path, stale)
    self.assertEqual(('NewReader',), recovered.schema.users)
    self.assertFalse(recovered.stale)
    self.assertIsNone(recovered.availability)

  def test_configuration_change_can_disable_or_select_another_snapshot(self):
    self.write_snapshot({'schemaVersion': 1, 'user': 'Reader', 'relations': [], 'users': ['Reader']})
    initial = load_snapshot(self.path)
    disabled = refresh_snapshot(None, initial)
    self.assertIsNone(disabled.schema)
    self.assertFalse(disabled.stale)
    self.assertIn('not configured', disabled.availability)
    other = self.path.with_name('other.json')
    other.write_text('{"schemaVersion": 1, "user": "Other", "relations": [], "users": ["Other"]}',
                     encoding='utf-8')
    changed = refresh_snapshot(other, disabled)
    self.assertEqual(('Other',), changed.schema.users)
    self.assertFalse(changed.stale)
    self.assertIsNone(changed.availability)

  def test_directory_path_is_an_availability_failure(self):
    snapshot = load_snapshot(self.path.parent)
    self.assertIsNone(snapshot.schema)
    self.assertFalse(snapshot.stale)
    self.assertIn('unavailable', snapshot.availability)

  def test_snapshot_loading_reads_only_the_explicit_file_without_external_access(self):
    self.write_snapshot({
      'schemaVersion': 1, 'user': 'Reader', 'relations': [], 'users': ['Reader'],
      'credentialPath': '/never/read/credentials', 'runtimeCommand': ['must-not-run'],
      'connection': {'host': 'must-not-connect'},
    })
    real_open = io.open

    def open_snapshot(file, *args, **kwargs):
      self.assertEqual(self.path, Path(file), 'loader opened an unrelated path')
      return real_open(file, *args, **kwargs)

    with ExitStack() as guards:
      guards.enter_context(patch('io.open', side_effect=open_snapshot))
      for target in ('builtins.open', 'os.open', 'os.getenv', 'os.system',
                     'subprocess.Popen', 'socket.socket', 'socket.create_connection', 'getpass.getpass'):
        guards.enter_context(patch(target, side_effect=AssertionError('snapshot attempted external access')))
      for method in ('__getitem__', '__iter__', '__contains__'):
        guards.enter_context(patch.object(type(os.environ), method,
                                         side_effect=AssertionError('snapshot read environment credentials')))
      snapshot = load_snapshot(self.path)
      self.assertEqual(Schema('Reader', (), ('Reader',)), snapshot.schema)
      self.assertEqual(snapshot, refresh_snapshot(self.path, snapshot))
      text = 'SHOW GRANTS FOR Re'
      self.assertEqual(['Reader'], [item.text for item in
                                   complete(text, len(text), PROFILE, snapshot.schema).items])

  def test_lone_surrogates_in_metadata_are_unavailable(self):
    for field in ('user', 'owner', 'name', 'columns', 'users', 'database', 'indexes'):
      for surrogate in ('\ud800', '\udfff'):
        with self.subTest(field=field, surrogate=repr(surrogate)):
          data = {
            'schemaVersion': 1, 'user': 'Reader',
            'relations': [{'owner': 'Reader', 'name': 'Code', 'kind': 'CLASS', 'columns': []}],
          }
          value = [surrogate] if field in ('columns', 'users', 'indexes') else surrogate
          if field in ('user', 'users', 'database'):
            data[field] = value
          else:
            data['relations'][0][field] = value
          self.path.write_text(json.dumps(data, ensure_ascii=True), encoding='utf-8')
          snapshot = load_snapshot(self.path)
          self.assertIsNone(snapshot.schema)
          self.assertIn(field, snapshot.availability)
          self.assertIn('Unicode', snapshot.availability)

  def test_valid_escaped_emoji_pairs_preserve_completion_text(self):
    data = {
      'schemaVersion': 1, 'user': 'Reader', 'users': ['😀 Reader'],
      'relations': [{'owner': 'Reader', 'name': '😀 목록', 'kind': 'CLASS', 'columns': ['😀 이름']}],
    }
    self.path.write_text(json.dumps(data, ensure_ascii=True), encoding='utf-8')
    snapshot = load_snapshot(self.path)
    self.assertIsNone(snapshot.availability)
    self.assertEqual('😀 목록', snapshot.schema.relations[0].name)
    self.assertEqual(('😀 이름',), snapshot.schema.relations[0].columns)
    text = 'select * from [😀 '
    self.assertEqual(['[😀 목록]'], [item.text for item in
                                 complete(text, len(text), PROFILE, snapshot.schema).items])


if __name__ == '__main__':
  unittest.main()
