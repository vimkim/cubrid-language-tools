"""Golden observations captured from the preserved checkpoint's public suggest API."""

from contextlib import ExitStack
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from cubrid_language import Relation, Schema, Span, complete


PROFILE = 'cubrid-11.5.0.2704-cc94778'


class CompletionParityTest(unittest.TestCase):

  @classmethod
  def setUpClass(cls):
    fixture = Path(__file__).parent / 'fixtures' / 'completion-ea796ad.json'
    data = json.loads(fixture.read_text(encoding='utf-8'))
    cls.cases = data['cases']
    cls.schemas = tuple(Schema(
      user=value['user'],
      relations=tuple(Relation(
        owner=relation['owner'], name=relation['name'], kind=relation['kind'],
        columns=tuple(relation['columns']), system=relation['system'],
        indexes=tuple(relation['indexes']),
      ) for relation in value['relations']),
      users=tuple(value['users']), database=value['database'],
    ) for value in data['schemas'])

  def test_original_suggestion_values_and_ranges_match_the_public_interface(self):
    for case in self.cases:
      with self.subTest(text=case['text'], cursor=case['cursor'], schema=case['schema']):
        result = complete(case['text'], case['cursor'], PROFILE, self.schemas[case['schema']])
        self.assertIs(type(result.replacement), Span)
        self.assertEqual(case['replacement'], [result.replacement.start, result.replacement.end])
        self.assertEqual(case['items'], [[item.text, item.label, item.kind, item.detail]
                                        for item in result.items])
        self.assertEqual(case['allowed'], result.allowed)

  def test_the_entire_checkpoint_corpus_is_deterministic_without_system_io(self):
    with ExitStack() as guards:
      for target in ('builtins.open', 'builtins.print', 'io.open', 'os.open',
                     'os.listdir', 'os.scandir', 'os.stat', 'os.getenv', 'os.putenv',
                     'os.system', 'subprocess.Popen', 'socket.socket',
                     'socket.create_connection', 'os.isatty', 'termios.tcgetattr',
                     'termios.tcsetattr'):
        guards.enter_context(patch(target, side_effect=AssertionError('completion attempted I/O')))
      for method in ('__getitem__', '__iter__', '__contains__', '__setitem__', '__delitem__'):
        guards.enter_context(patch.object(type(os.environ), method,
                                         side_effect=AssertionError('completion accessed the environment')))
      for case in self.cases:
        with self.subTest(text=case['text'], cursor=case['cursor'], schema=case['schema']):
          arguments = (case['text'], case['cursor'], PROFILE, self.schemas[case['schema']])
          self.assertEqual(complete(*arguments), complete(*arguments))


if __name__ == '__main__':
  unittest.main()
