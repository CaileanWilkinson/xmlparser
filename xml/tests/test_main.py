import unittest

from xml import xml


class Test(unittest.TestCase):
    """
        Basic tests
    """
    def test_normalises_newlines(self):
        with self.subTest("#D"):
            document = xml.parse("<root>\u000d</root>")
            self.assertEqual("\u000a", document.root.text[0].text)
        with self.subTest("#D#A"):
            document = xml.parse("<root>\u000d\u000a</root>")
            self.assertEqual("\u000a", document.root.text[0].text)
