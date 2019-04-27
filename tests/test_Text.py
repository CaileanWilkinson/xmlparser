from tests.mocks.MockDTD import MockDTD
from tests.mocks.MockEntity import MockEntity
from xml_parser.content.Text import TextFactory
from xml_parser.errors import XMLError
import unittest


class TextTests(unittest.TestCase):
    def test_concatenates_text_blocks(self):
        text_factory = TextFactory(MockDTD())
        text_factory.add_text("Some text")
        text_factory.add_text(" and some more text")
        text = text_factory.pop_text_object()

        self.assertEqual("Some text and some more text", text.text)

    def test_pops_text_object(self):
        text_factory = TextFactory(MockDTD())

        text_factory.add_text("Some text")
        text1 = text_factory.pop_text_object()

        text_factory.add_text("Some other text")
        text2 = text_factory.pop_text_object()

        self.assertEqual("Some text", text1.text)
        self.assertEqual("Some other text", text2.text)

    """
        ================
        PARSE-END TESTS
        ================
    """

    def test_ends_parse_at_processing_instruction(self):
        xml = "This is some text blah blah blah <?PROCESSINGINSTRUCTION should be returned?> Some more text"
        text_factory = TextFactory(MockDTD())
        unparsed_xml = text_factory.add_text(xml)
        text = text_factory.pop_text_object()

        self.assertEqual("<?PROCESSINGINSTRUCTION should be returned?> Some more text",
                         unparsed_xml)
        self.assertEqual("This is some text blah blah blah ", text.text)

    def test_ends_parse_at_comment(self):
        xml = "This is some text blah blah blah <!--This is a comment and should be returned--> Some more text"
        text_factory = TextFactory(MockDTD())
        unparsed_xml = text_factory.add_text(xml)
        text = text_factory.pop_text_object()

        self.assertEqual("<!--This is a comment and should be returned--> Some more text",
                         unparsed_xml)
        self.assertEqual("This is some text blah blah blah ", text.text)

    def test_ends_parse_at_element(self):
        with self.subTest("Nonempty element"):
            xml = "This is some text blah blah blah <Element> Some more text</Element>"
            text_factory = TextFactory(MockDTD())
            unparsed_xml = text_factory.add_text(xml)
            text = text_factory.pop_text_object()

            self.assertEqual("<Element> Some more text</Element>", unparsed_xml)
            self.assertEqual("This is some text blah blah blah ", text.text)

        with self.subTest("Self-closing element"):
            xml = "This is some text blah blah blah <Element/> Some more text"
            text_factory = TextFactory(MockDTD())
            unparsed_xml = text_factory.add_text(xml)
            text = text_factory.pop_text_object()

            self.assertEqual("<Element/> Some more text", unparsed_xml)
            self.assertEqual("This is some text blah blah blah ", text.text)

    def test_ends_parse_at_general_entity(self):
        xml = "This is some text blah blah blah &entity; Some more text"
        text_factory = TextFactory(MockDTD())
        unparsed_xml = text_factory.add_text(xml)
        text = text_factory.pop_text_object()

        self.assertEqual("&entity; Some more text", unparsed_xml)
        self.assertEqual("This is some text blah blah blah ", text.text)

    """
        ======================
        FORBIDDEN CHARACTERS
        ======================
    """

    def test_forbidden_characters(self):
        for char in ["\u0001", "\u0003", "\u0010", "\ufffe", "\uffff"]:
            with self.subTest(f"Char: {char}"):
                text_factory = TextFactory(MockDTD())
                text_factory.add_text(f"Some text with a forbidden {char} <end/>")
                with self.assertRaises(XMLError):
                    text_factory.pop_text_object()

    def test_no_cdata_end_tags(self):
        text_factory = TextFactory(MockDTD())
        with self.assertRaises(XMLError):
            text_factory.add_text("Some text with a forbidden ]]> <end/>")
            text_factory.pop_text_object()

    """
        =================
        ENTITY EXPANSION
        =================
    """

    def test_expands_decimal_char_references(self):
        for num, char in [(118, "v"), (279, "ė"), (632, "ɸ"), (986, "Ϛ"), (1948, "ޜ")]:
            with self.subTest(f"&#{num}; -> {char}"):
                text_factory = TextFactory(MockDTD())
                text_factory.add_text(f"Char&#{num};<end/>")
                text = text_factory.pop_text_object()
                self.assertEqual(f"Char{char}", text.text)

    def test_expands_hexadecimal_char_references(self):
        for num, char in [("76", "v"), ("117", "ė"), ("278", "ɸ"), ("3da", "Ϛ"), ("79c", "ޜ")]:
            with self.subTest(f"&#{num}; -> {char}"):
                text_factory = TextFactory(MockDTD())
                text_factory.add_text(f"Char&#x{num};<end/>")
                text = text_factory.pop_text_object()
                self.assertEqual(f"Char{char}", text.text)

    def test_ignores_parameter_entities(self):
        text_factory = TextFactory(MockDTD())
        text_factory.add_text("Some text %param_entity; some more text <end/>")
        text = text_factory.pop_text_object()
        self.assertEqual("Some text %param_entity; some more text ", text.text)


class CDataTests(unittest.TestCase):
    """
        ============
        CDATA TESTS    
        ============
    """

    def test_removes_tags(self):
        text_factory = TextFactory(MockDTD())
        text_factory.add_text(
            "Some text with a<![CDATA[ cdata section which]]> doesn't get parsed<end/>")
        text = text_factory.pop_text_object()
        self.assertEqual("Some text with a cdata section which doesn't get parsed", text.text)

    def test_ignores_markup(self):
        with self.subTest("Comments"):
            text_factory = TextFactory(MockDTD())
            text_factory.add_text(
                "Some text and a<![CDATA[ <!-- comment which should not be parsed -->]]></end>")
            text = text_factory.pop_text_object()
            self.assertEqual("Some text and a <!-- comment which should not be parsed -->",
                             text.text)

        with self.subTest("Processing Instruction"):
            text_factory = TextFactory(MockDTD())
            text_factory.add_text(
                "Some text and a<![CDATA[ <?PI which should not be parsed?>]]></end>")
            text = text_factory.pop_text_object()
            self.assertEqual("Some text and a <?PI which should not be parsed?>", text.text)

        with self.subTest("Element"):
            text_factory = TextFactory(MockDTD())
            text_factory.add_text(
                "Some text and an<![CDATA[ <elementtag> which should not be parsed </elementtag> ]]></end>")
            text = text_factory.pop_text_object()
            self.assertEqual(
                "Some text and an <elementtag> which should not be parsed </elementtag> ",
                text.text)

    def test_ignores_entity_references(self):
        with self.subTest("General entity references"):
            entity = MockEntity("entity", expansion_text="SOMEVALUE")
            dtd = MockDTD(general={"entity": entity})

            text_factory = TextFactory(dtd)
            text_factory.add_text(
                "Some text and an<![CDATA[ &entity; which should not be parsed ]]></end>")
            text = text_factory.pop_text_object()
            self.assertEqual("Some text and an &entity; which should not be parsed ", text.text)
        with self.subTest("Character references"):
            text_factory = TextFactory(dtd)
            text_factory.add_text(
                "Some text and a<![CDATA[ char reference &#109; which should not be parsed ]]></end>")
            text = text_factory.pop_text_object()
            self.assertEqual("Some text and a char reference &#109; which should not be parsed ",
                             text.text)

    def test_forbidden_characters(self):
        for char in ["\u0001", "\u0003", "\u0010", "\ufffe", "\uffff"]:
            with self.subTest(f"Char: {char}"):
                text_factory = TextFactory(MockDTD())
                text_factory.add_text(
                    f"Some cdata text with a forbidden <![CDATA[{char} ]]> <end/>")
                with self.assertRaises(XMLError):
                    text_factory.pop_text_object()
