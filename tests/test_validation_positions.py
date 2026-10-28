import unittest
import tracemalloc

from cubrid_language.validation import DocumentMap


class DocumentMapTests(unittest.TestCase):
    def test_original_korean_emoji_and_crlf_boundaries(self):
        doc = DocumentMap("가😀x\r\nSELECT 1;")
        self.assertEqual(doc.to_byte(2), 7)
        self.assertEqual(doc.from_byte(7), 2)
        self.assertEqual(doc.to_position(2), (0, 3))
        self.assertEqual(doc.from_position(0, 3), 2)
        self.assertEqual(doc.to_position(5), (1, 0))
        self.assertEqual(doc.to_byte(5), 10)
        self.assertEqual(doc.to_position(14), (1, 9))
        self.assertEqual(doc.human_location(2), (1, 3))

    def test_positions_reject_split_encodings_and_line_terminators(self):
        doc = DocumentMap("가😀x\r\n")
        for call, args in ((doc.from_byte, (1,)), (doc.from_byte, (4,)),
                           (doc.from_position, (0, 2)), (doc.from_position, (0, 5)),
                           (doc.to_position, (4,)), (doc.to_byte, (-1,)),
                           (doc.from_position, (2, 0)), (doc.from_byte, (11,)),
                           (doc.to_byte, (True,))):
            with self.subTest(args=args), self.assertRaises(ValueError):
                call(*args)
        self.assertEqual(doc.to_position(5), (1, 0))
        self.assertEqual(doc.from_position(1, 0), 5)

    def test_empty_document_and_empty_lines_have_eof_positions(self):
        self.assertEqual(DocumentMap("").from_position(0, 0), 0)
        self.assertEqual(DocumentMap("\n\r\n").to_position(3), (2, 0))
        with self.assertRaises(ValueError):
            DocumentMap("\ud800")

    def test_large_document_maps_keep_compact_storage_and_unicode_roundtrips(self):
        text = "가😀x\r\n" * 200_000
        tracemalloc.start()
        try:
            doc = DocumentMap(text)
            _, peak = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()
        self.assertLess(peak, 32 * 1024 * 1024)
        for offset in (0, 1, 2, 5, 999_997, len(text)):
            self.assertEqual(doc.from_byte(doc.to_byte(offset)), offset)
            self.assertEqual(doc.from_position(*doc.to_position(offset)), offset)
