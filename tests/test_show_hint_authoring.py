import unittest

from cubrid_language import complete
from cubrid_language.validation import PROFILE, Validator


class ShowHintAuthoringTests(unittest.TestCase):
    def test_hint_completion_replaces_whole_word(self):
        text = 'SELECT /*+ USE_NLwrong */ 1;'
        result = complete(text, text.index('wrong'), PROFILE)
        self.assertTrue(result.allowed)
        self.assertEqual(text[result.replacement.start:result.replacement.end], 'USE_NLwrong')
        self.assertIn('USE_NL', [item.text for item in result.items])

    def test_unknown_hint_survives_missing_native_runtime(self):
        text = 'SELECT /*+ NOT_A_HINT */ 1;'
        with Validator() as validator:
            result = validator.validate(text, PROFILE, 'sql')
        self.assertEqual(result.status, 'tool-error')
        self.assertIn('CUBRID-T1001', [d.code for d in result.diagnostics])
        warning = next(d for d in result.diagnostics if d.code == 'CUBRID-A1001')
        self.assertEqual((warning.severity, warning.category), ('warning', 'authoring'))
        self.assertEqual(text[warning.span.start:warning.span.end], 'NOT_A_HINT')
