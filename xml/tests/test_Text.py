from xml.tests.mocks.MockEntity import MockEntity
from xml.classes.content.Text import Text
from xml.classes.Error import XMLError
import unittest


class TextTests(unittest.TestCase):

    """
        ================
        PARSE-END TESTS
        ================
        These tests ensure that the Text class only parses the provided xml as far as it is character data,
        and that occurrences of markup are returned to the parent class for proper processing
    """
    def test_ends_parse_at_processing_instruction(self):
        xml = "This is some text blah blah blah <?PROCESSINGINSTRUCTION should be returned?> Some more text"
        text = Text()
        unparsed_xml = text.add_text(xml)
        text.check_wellformedness()

        self.assertEqual("<?PROCESSINGINSTRUCTION should be returned?> Some more text", unparsed_xml)
        self.assertEqual("This is some text blah blah blah ", text.text)

    def test_ends_parse_at_comment(self):
        xml = "This is some text blah blah blah <!--This is a comment and should be returned--> Some more text"
        text = Text()
        unparsed_xml = text.add_text(xml)
        text.check_wellformedness()

        self.assertEqual("<!--This is a comment and should be returned--> Some more text", unparsed_xml)
        self.assertEqual("This is some text blah blah blah ", text.text)

    def test_ends_parse_at_element(self):
        with self.subTest("Nonempty element"):
            xml = "This is some text blah blah blah <Element> Some more text</Element>"
            text = Text()
            unparsed_xml = text.add_text(xml)
            text.check_wellformedness()

            self.assertEqual("<Element> Some more text</Element>", unparsed_xml)
            self.assertEqual("This is some text blah blah blah ", text.text)

        with self.subTest("Self-closing element"):
            xml = "This is some text blah blah blah <Element/> Some more text"
            text = Text()
            unparsed_xml = text.add_text(xml)
            text.check_wellformedness()

            self.assertEqual("<Element/> Some more text", unparsed_xml)
            self.assertEqual("This is some text blah blah blah ", text.text)

    def test_ends_parse_at_general_entity(self):
        xml = "This is some text blah blah blah &entity; Some more text"
        text = Text()
        unparsed_xml = text.add_text(xml)
        text.check_wellformedness()

        self.assertEqual("&entity; Some more text", unparsed_xml)
        self.assertEqual("This is some text blah blah blah ", text.text)

    """
        =================================
        ENTITY REFERENCE EXPANSION TESTS
        =================================
    """
    def test_expands_decimal_char_references(self):
        for num, char in [(118, "v"), (279, "ė"), (632, "ɸ"), (986, "Ϛ"), (1948, "ޜ")]:
            with self.subTest(f"&#{num}; -> {char}"):
                text = Text()
                text.add_text(f"Char&#{num};<end/>")
                text.check_wellformedness()
                self.assertEqual(f"Char{char}", text.text)

    def test_expands_hexadecimal_char_references(self):
        for num, char in [("76", "v"), ("117", "ė"), ("278", "ɸ"), ("3da", "Ϛ"), ("79c", "ޜ")]:
            with self.subTest(f"&#{num}; -> {char}"):
                text = Text()
                text.add_text(f"Char&#x{num};<end/>")
                text.check_wellformedness()
                self.assertEqual(f"Char{char}", text.text)

    def test_ignores_parameter_entities(self):
        text = Text()
        text.add_text("Some text %param_entity; some more text <end/>")
        text.check_wellformedness()
        self.assertEqual("Some text %param_entity; some more text ", text.text)

    """
        ============
        CDATA TESTS    
        ============
    """
    def test_removes_cdata_tags(self):
        text = Text()
        text.add_text("Some text with a<![CDATA[ cdata section which]]> doesn't get parsed<end/>")
        text.check_wellformedness()
        self.assertEqual("Some text with a cdata section which doesn't get parsed", text.text)

    def test_ignores_cdata_markup(self):
        with self.subTest("Comments"):
            text = Text()
            text.add_text("Some text and a<![CDATA[ <!-- comment which should not be parsed -->]]></end>")
            text.check_wellformedness()
            self.assertEqual("Some text and a <!-- comment which should not be parsed -->", text.text)

        with self.subTest("Processing Instruction"):
            text = Text()
            text.add_text("Some text and a<![CDATA[ <?PI which should not be parsed?>]]></end>")
            text.check_wellformedness()
            self.assertEqual("Some text and a <?PI which should not be parsed?>", text.text)

        with self.subTest("Element"):
            text = Text()
            text.add_text("Some text and an<![CDATA[ <elementtag> which should not be parsed </elementtag> ]]></end>")
            text.check_wellformedness()
            self.assertEqual("Some text and an <elementtag> which should not be parsed </elementtag> ", text.text)

    def test_ignores_cdata_entity_references(self):
        with self.subTest("General entity references"):
            entity = MockEntity("entity", expansion_text="SOMEVALUE")

            text = Text()
            text.add_text("Some text and an<![CDATA[ &entity; which should not be parsed ]]></end>")
            text.check_wellformedness()
            self.assertEqual("Some text and an &entity; which should not be parsed ", text.text)
        with self.subTest("Character references"):
            text = Text()
            text.add_text("Some text and a<![CDATA[ char reference &#109; which should not be parsed ]]></end>")
            text.check_wellformedness()
            self.assertEqual("Some text and a char reference &#109; which should not be parsed ", text.text)

    def test_cdata_forbidden_characters(self):
        for char in ["\u0001", "\u0003", "\u0010", "\ufffe", "\uffff"]:
            with self.subTest(f"Char: {char}"):
                text = Text()
                text.add_text(f"Some cdata text with a forbidden <![CDATA[{char} ]]> <end/>")
                with self.assertRaises(XMLError):
                    text.check_wellformedness()

    """
        ======================
        WELL-FORMEDNESS TESTS
        ======================
    """

    def test_forbidden_characters(self):
        for char in ["\u0001", "\u0003", "\u0010", "\ufffe", "\uffff"]:
            with self.subTest(f"Char: {char}"):
                text = Text()
                text.add_text(f"Some text with a forbidden {char} <end/>")
                with self.assertRaises(XMLError):
                    text.check_wellformedness()

    def test_no_cdata_end_tags(self):
        text = Text()
        with self.assertRaises(XMLError):
            text.add_text("Some text with a forbidden ]]> <end/>")
            text.check_wellformedness()
