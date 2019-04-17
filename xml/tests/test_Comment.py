from classes.Comment import Comment
from classes.Error import XMLError
import unittest


class CommentTests(unittest.TestCase):
    def test_stops_parsing(self):
        comment = Comment("<!-- A comment which should end here--> And more text")
        unparsed_xml = comment.parse_to_end({})
        self.assertEqual(" And more text", unparsed_xml)

    """
        ======================
        WELL-FORMEDNESS TESTS
        ======================
    """

    def test_forbidden_characters(self):
        for char in ["\u0001", "\u0003", "\u0010", "\ufffe", "\uffff"]:
            with self.subTest(f"Char: {char}"):
                comment = Comment(f"<!--A comment with {char} --> Text <end/>")
                with self.assertRaises(XMLError):
                    comment.parse_to_end({})

    def test_double_hyphen(self):
        comment = Comment(f"<!--A comment with -- --> Text <end/>")
        with self.assertRaises(XMLError):
            comment.parse_to_end({})

    def test_triple_hyphen(self):
        comment = Comment(f"<!--A comment with ---> Text <end/>")
        with self.assertRaises(XMLError):
            comment.parse_to_end({})
