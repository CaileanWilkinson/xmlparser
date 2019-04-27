import unittest

import xml_parser


class Test(unittest.TestCase):
    """
        Basic tests
    """
    def test_normalises_newlines(self):
        with self.subTest("#D"):
            document = xml_parser.parse_string("<root>\u000d</root>")
            self.assertEqual("\u000a", document.file.text[0].text)
        with self.subTest("#D#A"):
            document = xml_parser.parse_string("<root>\u000d\u000a</root>")
            self.assertEqual("\u000a", document.file.text[0].text)
