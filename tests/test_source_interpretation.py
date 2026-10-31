import unittest

from cubrid_language import authoring_diagnostics, complete
from cubrid_language.validation import PROFILE


class SourceInterpretationTests(unittest.TestCase):
    def test_unclosed_command_quote_keeps_region_local_warnings(self):
        text = ";help 'broken\nSELECT /*+ BOGUS */ 1;"
        start = text.index('BOGUS')
        for mode in ('sql', 'csql'):
            with self.subTest(mode=mode):
                findings = authoring_diagnostics(text, PROFILE, mode)
                self.assertEqual([(d.code, d.span.start, d.span.end) for d in findings],
                                 [('CUBRID-A1001', start, start + 5)])
        result = complete(text, start + 2, PROFILE)
        self.assertFalse(result.allowed)
        self.assertEqual((result.replacement.start, result.replacement.end, result.items),
                         (start + 2, start + 2, ()))

    def test_trigger_cutoff_and_command_separated_recovery(self):
        cases = (
            ('SELECT /*+ BOGUS */ 1; CREATE TRIGGER t; SELECT /*+ BOGUS */ 1;', (0,)),
            ('CREATE OR REPLACE TRIGGER t; SELECT /*+ BOGUS */ 1;', ()),
            ('CREATE TRIGGERED t; SELECT /*+ BOGUS */ 1;', (0,)),
            ('CREATE TRIGGER t;\n;help\nSELECT /*+ BOGUS */ 1;', (0,)),
        )
        for text, expected_indexes in cases:
            with self.subTest(text=text):
                starts = [i for i in range(len(text)) if text.startswith('BOGUS', i)]
                expected = [starts[i] for i in expected_indexes]
                findings = authoring_diagnostics(text, PROFILE, 'csql')
                self.assertEqual([(d.code, d.span.start, d.span.end) for d in findings],
                                 [('CUBRID-A1001', i, i + 5) for i in expected])
                for start in starts:
                    result = complete(text, start + 2, PROFILE)
                    self.assertEqual(result.allowed, start in expected)
                    self.assertEqual((result.replacement.start, result.replacement.end),
                                     (start, start + 5) if start in expected else (start + 2, start + 2))

    def test_input_validation_precedes_unknown_profile_return(self):
        cases = (
            ((None, PROFILE, 'sql'), 'expected Unicode text, profile, and sql or csql mode'),
            (('a', None, 'bad'), 'expected Unicode text, profile, and sql or csql mode'),
            (('a', 'unknown', 'bad'), 'expected Unicode text, profile, and sql or csql mode'),
            (('\ud800', 'unknown', 'sql'), 'input must contain valid Unicode scalars'),
            (('\0', 'unknown', 'sql'), 'invalid profile or document'),
        )
        for args, message in cases:
            with self.subTest(args=args):
                with self.assertRaisesRegex(ValueError, '^' + message + '$'):
                    authoring_diagnostics(*args)
        self.assertEqual(authoring_diagnostics('SELECT /*+ BOGUS */ 1;', 'unknown'), ())


if __name__ == '__main__':
    unittest.main()
