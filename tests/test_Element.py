from xml_parser.content.Element import ElementFactory
from tests.mocks.MockDTD import MockDTD
from tests.mocks.MockEntity import MockEntity
from xml_parser.errors import XMLError, DisallowedCharacterError
import unittest


class ElementTests(unittest.TestCase):
    # todo - More tests

    """
        ================
        ATTRIBUTE TESTS
        ================
    """

    def test_multiple_attribute_parsing(self):
        xml = "<Element attr1='Value1' attr2='Value2'/> some text"
        element, _ = ElementFactory.parse_from_xml(xml, MockDTD())

        self.assertEqual({"attr1": "Value1", "attr2": "Value2"}, element.attributes)

    def test_repeated_attribute(self):
        xml = "<Element attr='value' attr='value'/>"
        with self.assertRaises(XMLError):
            ElementFactory.parse_from_xml(xml, MockDTD())

    """
        ================
        PARSE-END TESTS
        ================
    """

    def test_ends_parse_on_close(self):
        with self.subTest("Self-closing"):
            xml = "<Element/> some text"
            element, unparsed_xml = ElementFactory.parse_from_xml(xml, MockDTD())

            self.assertEqual(" some text", unparsed_xml)
        with self.subTest("Open"):
            xml = "<Element>some text</Element> some more text"
            element, unparsed_xml = ElementFactory.parse_from_xml(xml, MockDTD())

            self.assertEqual(" some more text", unparsed_xml)

    """ 
        ======================
        WELL-FORMEDNESS TESTS
        ======================
    """

    def test_mismatched_tags(self):
        xml = "<Element1>some text</Element2> some more text"

        with self.assertRaises(XMLError):
            ElementFactory.parse_from_xml(xml, MockDTD())


class NameTests(unittest.TestCase):
    def test_name_parsing(self):
        with self.subTest("/>"):
            xml = "Element/>"
            element, _ = ElementFactory.parse_name(xml, "")

            self.assertEqual("Element", element)

        with self.subTest(">"):
            xml = "Element>"
            element, _ = ElementFactory.parse_name(xml, "")

            self.assertEqual("Element", element)

        with self.subTest("whitespace"):
            xml = "Element "
            element, _ = ElementFactory.parse_name(xml, "")

            self.assertEqual("Element", element)

    def test_parse_ends_after_name(self):
        with self.subTest("/>"):
            xml = "Element/>BLAH"
            _, remaining_xml = ElementFactory.parse_name(xml, "")

            self.assertEqual("/>BLAH", remaining_xml)

        with self.subTest(">"):
            xml = "Element>BLAH"
            _, remaining_xml = ElementFactory.parse_name(xml, "")

            self.assertEqual(">BLAH", remaining_xml)

        with self.subTest("whitespace"):
            xml = "Element BLAH"
            _, remaining_xml = ElementFactory.parse_name(xml, "")

            self.assertEqual(" BLAH", remaining_xml)

    """
        =====================
        FORBIDDEN CHARACTERS
        =====================
    """

    def test_forbidden_name_start_characters(self):
        for char in ["-", ".", "0", "7", "\u0305"]:
            with self.subTest(char):
                xml = f"{char}xmlElement>"
                with self.assertRaises(DisallowedCharacterError):
                    ElementFactory.parse_name(xml, "")

    def test_forbidden_name_characters(self):
        for char in ["\u0001", "\u0003", "\u0010", "\ufffe", "\uffff"]:
            with self.subTest(char):
                xml = f"{char}xmlElement>"
                with self.assertRaises(DisallowedCharacterError):
                    ElementFactory.parse_name(xml, "")

    def test_forbidden_xml_name(self):
        with self.subTest("xml"):
            xml = f"xml "

            with self.assertRaises(XMLError):
                ElementFactory.parse_name(xml, "")

        with self.subTest("XmL"):
            xml = f"XmL "

            with self.assertRaises(XMLError):
                ElementFactory.parse_name(xml, "")

        with self.subTest("xmlBlah"):
            xml = f"xmlBlah "

            with self.assertRaises(XMLError):
                ElementFactory.parse_name(xml, "")

        with self.subTest("XmLBlah"):
            xml = f"XmLBlah "

            with self.assertRaises(XMLError):
                ElementFactory.parse_name(xml, "")


class AttributeNameTests(unittest.TestCase):
    def test_name_parsing(self):
        xml = "Name =  "
        name, _ = ElementFactory.parse_attribute_name(xml, "")

        self.assertEqual("Name", name)

    def test_parse_ends_after_name(self):
        xml = "Name = BLAH"
        _, remaining_xml = ElementFactory.parse_attribute_name(xml, "")

        self.assertEqual("BLAH", remaining_xml)

    """
        =====================
        FORBIDDEN CHARACTERS
        =====================
    """

    def test_forbidden_name_start_characters(self):
        for char in ["-", ".", "0", "7", "\u0305"]:
            with self.subTest(char):
                xml = f"{char}name = "
                with self.assertRaises(DisallowedCharacterError):
                    ElementFactory.parse_attribute_name(xml, "")

    def test_forbidden_name_characters(self):
        for char in ["\u0001", "\u0003", "\u0010", "\ufffe", "\uffff"]:
            with self.subTest(char):
                xml = f"{char}name = "
                with self.assertRaises(DisallowedCharacterError):
                    ElementFactory.parse_attribute_name(xml, "")

    def test_forbidden_xml_name(self):
        with self.subTest("xml"):
            xml = f"xml = "

            with self.assertRaises(XMLError):
                ElementFactory.parse_attribute_name(xml, "")

        with self.subTest("XmL"):
            xml = f"XmL = "

            with self.assertRaises(XMLError):
                ElementFactory.parse_attribute_name(xml, "")

        with self.subTest("xmlBlah"):
            xml = f"xmlBlah = "

            with self.assertRaises(XMLError):
                ElementFactory.parse_attribute_name(xml, "")

        with self.subTest("XmLBlah"):
            xml = f"XmLBlah = "

            with self.assertRaises(XMLError):
                ElementFactory.parse_attribute_name(xml, "")


class AttributeValueTests(unittest.TestCase):
    def test_attribute_parsing(self):
        with self.subTest("\'"):
            xml = "'value'"
            value, _ = ElementFactory.parse_attribute_value(xml, "", "", "", MockDTD())

            self.assertEqual("value", value)
        with self.subTest("\""):
            xml = '"value"'
            value, _ = ElementFactory.parse_attribute_value(xml, "", "", "", MockDTD())

            self.assertEqual("value", value)

    def test_parse_ends_after_value(self):
        with self.subTest("\'"):
            xml = "'value'BLAH"
            _, remaining_xml = ElementFactory.parse_attribute_value(xml, "", "", "", MockDTD())

            self.assertEqual("BLAH", remaining_xml)
        with self.subTest("\""):
            xml = '"value"BLAH'
            _, remaining_xml = ElementFactory.parse_attribute_value(xml, "", "", "", MockDTD())

            self.assertEqual("BLAH", remaining_xml)

    """
        =====================
        FORBIDDEN CHARACTERS
        =====================
    """
    def test_forbidden_characters(self):
        for char in ["<", "&", "\u0001", "\u0003", "\u0010", "\ufffe", "\uffff"]:
            with self.subTest(char):
                xml = f"'Blah{char}'"
                with self.assertRaises(XMLError):
                    ElementFactory.parse_attribute_value(xml, "", "", "", MockDTD())

    def test_forbidden_entity_replacement_character(self):
        with self.subTest("Disallow <"):
            entity = MockEntity("entity", expansion_text="<")
            dtd = MockDTD(general={"entity": entity})

            xml = "'blah&entity;blah'"
            with self.assertRaises(XMLError):
                ElementFactory.parse_attribute_value(xml, "", "", "", dtd)

        with self.subTest("Allow &lt;"):
            xml = "'blah&lt;blah'"
            value, _ = ElementFactory.parse_attribute_value(xml, "", "", "", MockDTD())

            self.assertEqual("blah<blah", value)

    """
        =================
        ENTITY EXPANSION
        =================
    """

    def test_general_entity_replacement(self):
        entity = MockEntity("entity", expansion_text="ENTITY TEXT")
        dtd = MockDTD(general={"entity": entity})

        xml = "'Entity &entity; text'"
        value, _ = ElementFactory.parse_attribute_value(xml, "", "", "", dtd)

        self.assertEqual("Entity ENTITY TEXT text", value)

    def test_missing_general_entity(self):
        xml = "'Entity &entity; text'"

        with self.assertRaises(XMLError):
            ElementFactory.parse_attribute_value(xml, "", "", "", MockDTD())

    def test_ignores_parameter_entity(self):
        xml = "'Entity %entity; text'"
        value, _ = ElementFactory.parse_attribute_value(xml, "", "", "", MockDTD())

        self.assertEqual("Entity %entity; text", value)

    def test_decimal_character_reference_replacement(self):
        for num, char in [(118, "v"), (279, "ė"), (632, "ɸ"), (986, "Ϛ"), (1948, "ޜ")]:
            with self.subTest(f"&#{num}; -> {char}"):
                xml = f"'Entity &#{num}; text'"
                value, _ = ElementFactory.parse_attribute_value(xml, "", "", "", MockDTD())

                self.assertEqual(f"Entity {char} text", value)

    def test_hexadecimal_character_reference_replacement(self):
        for num, char in [("76", "v"), ("117", "ė"), ("278", "ɸ"), ("3da", "Ϛ"), ("79c", "ޜ")]:
            with self.subTest(f"&#{num}; -> {char}"):
                xml = f"'Entity &#x{num}; text'"
                value, _ = ElementFactory.parse_attribute_value(xml, "", "", "", MockDTD())

                self.assertEqual(f"Entity {char} text", value)


    """
        ==========================
        WHITESPACE HANDLING TESTS
        ==========================
    """
    # todo - WS Tests


class ContentTests(unittest.TestCase):
    # todo - Test `parse_xml_block` function

    def test_nested_elements(self):
        xml = "<Element><SubElement><SubSubElement></SubSubElement></SubElement></Element>"
        element, _ = ElementFactory.parse_from_xml(xml, MockDTD())

        self.assertEqual("SubElement", element.content[0].name)
        self.assertEqual("SubElement", element.children[0].name)

        self.assertEqual("SubSubElement", element.content[0].content[0].name)
        self.assertEqual("SubSubElement", element.children[0].children[0].name)

    def test_nested_processing_instructions(self):
        xml = "<Element><?Target1?><?Target2 data?></Element>"
        element, _ = ElementFactory.parse_from_xml(xml, MockDTD())

        self.assertEqual("Target1", element.content[0].target)
        self.assertEqual("Target1", element.processing_instructions[0].target)

        self.assertEqual("Target2", element.content[1].target)
        self.assertEqual("Target2", element.processing_instructions[1].target)

    def test_nested_text(self):
        xml = "<Element>Some text here</Element>"
        element, _ = ElementFactory.parse_from_xml(xml, MockDTD())

        self.assertEqual("Some text here", element.content[0].text)
        self.assertEqual("Some text here", element.text[0].text)

    def test_nested_mixed(self):
        xml = "<Element>Some text<SubElement>More text</SubElement>  <!-- comment --><?Target data?></Element>"
        element, _ = ElementFactory.parse_from_xml(xml, MockDTD())

        self.assertEqual("Some text", element.content[0].text)
        self.assertEqual("Some text", element.text[0].text)

        self.assertEqual("SubElement", element.content[1].name)
        self.assertEqual("SubElement", element.children[0].name)
        self.assertEqual("More text", element.content[1].text[0].text)

        self.assertEqual("  ", element.content[2].text)
        self.assertEqual("  ", element.text[1].text)

        self.assertEqual("Target", element.content[3].target)
        self.assertEqual("Target", element.processing_instructions[0].target)

        self.assertEqual(4, len(element.content))

