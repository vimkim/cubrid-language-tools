"""Capture public suggestion observations from the preserved, read-only checkpoint.

This optional fixture generator is not imported by the package or its tests.
Run it with ``python -B`` to keep the checkpoint free of bytecode writes.
"""

import argparse
from dataclasses import asdict
import importlib
import io
import json
from pathlib import Path
import subprocess
import sys
import unittest


SOURCE_COMMIT = 'ea796ad6611fa0090003f9698e6d635b8978591a'


def main():
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument('checkpoint', type=Path)
  parser.add_argument('--output', type=Path,
                      default=Path(__file__).with_name('completion-ea796ad.json'))
  args = parser.parse_args()
  checkpoint = args.checkpoint.resolve()
  revision = subprocess.check_output(['git', '-C', str(checkpoint), 'rev-parse', 'HEAD'], text=True).strip()
  if revision != SOURCE_COMMIT:
    parser.error('checkpoint must be at ' + SOURCE_COMMIT)
  if subprocess.check_output(['git', '-C', str(checkpoint), 'status', '--porcelain'], text=True):
    parser.error('checkpoint must have no tracked or untracked changes')

  sys.dont_write_bytecode = True
  sys.path[:0] = [str(checkpoint / 'src'), str(checkpoint / 'tests')]
  legacy = importlib.import_module('csql_future.completion')
  original = legacy.suggest
  observations, schemas = {}, []

  def capture(text, cursor, schema=legacy.Schema(), message=''):
    result = original(text, cursor, schema, message)
    schema_value = asdict(schema)
    if schema_value not in schemas:
      schemas.append(schema_value)
    value = {
      'text': text,
      'cursor': cursor,
      'schema': schemas.index(schema_value),
      'replacement': [result.start, result.end],
      'items': [[item.text, item.label, item.kind, item.detail] for item in result.candidates],
      'allowed': result.allowed,
    }
    observations[json.dumps([text, cursor, value['schema']], ensure_ascii=False)] = value
    return result

  legacy.suggest = capture
  suite = unittest.TestSuite()
  source_tests = ('test_completion', 'test_command_completion')
  for name in source_tests:
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(importlib.import_module(name)))
  stream = io.StringIO()
  result = unittest.TextTestRunner(stream=stream, verbosity=1).run(suite)
  if not result.wasSuccessful():
    raise SystemExit(stream.getvalue())
  fixture = {
    'sourceCommit': SOURCE_COMMIT,
    'sourceInterface': 'csql_future.completion.suggest',
    'sourceTests': ['tests/' + name + '.py' for name in source_tests],
    'sourceTestCount': result.testsRun,
    'schemas': schemas,
    'cases': list(observations.values()),
  }
  args.output.write_text(json.dumps(fixture, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
  print(f'Original tests: {result.testsRun}, observations: {len(observations)}, schemas: {len(schemas)}')


if __name__ == '__main__':
  main()
