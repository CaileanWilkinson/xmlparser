from tests.mocks.MockDTD import MockDTD
from xml_parser.content.Comment import CommentFactory
from xml_parser.errors import XMLError
import unittest


class CommentTests(unittest.TestCase):
    def test_stops_parsing(self):
        xml = "<!-- A comment which should end here--> And more text"
        unparsed_xml = CommentFactory.parse_from_xml(xml, MockDTD())

        self.assertEqual(" And more text", unparsed_xml)

    """
        =====================
        FORBIDDEN CHARACTERS
        =====================
    """

    def test_forbidden_characters(self):
        for char in ["\u0001", "\u0003", "\u0010", "\ufffe", "\uffff"]:
            with self.subTest(f"Char: {char}"):
                xml = f"<!--A comment with {char} --> Text <end/>"
                with self.assertRaises(XMLError):
                    CommentFactory.parse_from_xml(xml, MockDTD())

    def test_double_hyphen(self):
        xml = f"<!--A comment with -- --> Text <end/>"
        with self.assertRaises(XMLError):
            CommentFactory.parse_from_xml(xml, MockDTD())

    def test_triple_hyphen(self):
        xml = f"<!--A comment with ---> Text <end/>"
        with self.assertRaises(XMLError):
            CommentFactory.parse_from_xml(xml, MockDTD())
